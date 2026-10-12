"""
OpenTelemetry and Arize Phoenix tracing subsystem for Career-OS.

Provides:
  - Cryptographically derived, PII-free subject identification (``derive_subject_id``).
  - In-flight prompt and attribute sanitization (``scrub_pii``).
  - Custom ``PIIScrubbingSpanProcessor`` for OpenTelemetry spans.
  - Lifecycle initialization and teardown (``setup_tracing``, ``flush_tracing``).
  - Uniform LangGraph ``RunnableConfig`` factory (``build_run_config``).
"""

import hashlib
import hmac
import logging
import re
import uuid
from typing import Any

from langchain_core.runnables import RunnableConfig
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

from app.core.config import settings
from app.core.logging import get_correlation_id

logger = logging.getLogger("career_os.tracing")

_EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
)
_PHONE_PATTERN = re.compile(
    r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
)
_ADDRESS_PATTERN = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9\s.,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct|Circle|Cir|Terrace|Ter|Place|Pl)\b",
    re.IGNORECASE,
)
_GENERIC_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?!github\.com|linkedin\.com)[^\s<>\"']+",
    re.IGNORECASE,
)

_tracer_provider: TracerProvider | None = None
_instrumented: bool = False


def derive_subject_id(user_id: str | None) -> str:
    """
    Derive a deterministic, irreversible pseudonymous identifier for a candidate.

    Allows grouping all traces for a candidate across sessions without exposing PII
    or leaking underlying database UUIDs to Phoenix.
    """
    if not user_id or not user_id.strip():
        return "subj_anonymous"
    key = settings.SECRET_KEY.encode("utf-8")
    digest = hmac.new(key, user_id.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"subj_{digest}"


def scrub_pii(text: str) -> str:
    """
    Sanitize emails, phone numbers, and street addresses from prompt text.

    Preserves technical competencies, role titles, and standard software terms.
    """
    if not text:
        return text
    text = _EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
    text = _PHONE_PATTERN.sub("[PHONE_REDACTED]", text)
    text = _ADDRESS_PATTERN.sub("[ADDRESS_REDACTED]", text)
    return text


def _scrub_attribute_value(val: Any) -> Any:
    """Recursively scrub strings within span attribute values."""
    if isinstance(val, str):
        return scrub_pii(val)
    if isinstance(val, (list, tuple)):
        return type(val)(_scrub_attribute_value(x) for x in val)
    return val


class PIIScrubbingSpanProcessor(SpanProcessor):
    """
    OpenTelemetry SpanProcessor that intercepts span attributes before batch export
    and scrubs sensitive candidate PII from prompt inputs and outputs.
    """

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        """No-op on start."""
        pass

    def on_end(self, span: ReadableSpan) -> None:
        """Sanitize span attribute dictionaries before serialization."""
        if not settings.PHOENIX_ANONYMIZE_PII:
            return

        attrs = getattr(span, "_attributes", None)
        if attrs is not None:
            target_dict = getattr(attrs, "_dict", None)
            if isinstance(target_dict, dict):
                for k, v in list(target_dict.items()):
                    target_dict[k] = _scrub_attribute_value(v)
            elif isinstance(attrs, dict):
                for k, v in list(attrs.items()):
                    attrs[k] = _scrub_attribute_value(v)


def setup_tracing() -> None:
    """
    Initialize OpenTelemetry TracerProvider with Phoenix OTLP HTTP exporter
    and OpenInference LangChain instrumentation.

    Safely degrades if Phoenix is disabled, in test environments, or if
    the collector endpoint is unreachable.
    """
    global _tracer_provider, _instrumented
    if not settings.PHOENIX_ENABLED or settings.is_testing:
        logger.info(
            "Phoenix tracing disabled [enabled=%s, is_testing=%s]",
            settings.PHOENIX_ENABLED,
            settings.is_testing,
        )
        return

    if _instrumented:
        return

    try:
        sampler = TraceIdRatioBased(settings.PHOENIX_SAMPLING_RATE)
        provider = TracerProvider(sampler=sampler)
        provider.add_span_processor(PIIScrubbingSpanProcessor())

        exporter = OTLPSpanExporter(
            endpoint=settings.PHOENIX_COLLECTOR_ENDPOINT,
            timeout=2,
        )
        batch_processor = BatchSpanProcessor(
            exporter,
            max_queue_size=2048,
            export_timeout_millis=2000,
            schedule_delay_millis=5000,
        )
        provider.add_span_processor(batch_processor)

        trace.set_tracer_provider(provider)
        LangChainInstrumentor().instrument(tracer_provider=provider)

        _tracer_provider = provider
        _instrumented = True
        logger.info(
            "Arize Phoenix OpenTelemetry tracing initialized [endpoint=%s, project=%s]",
            settings.PHOENIX_COLLECTOR_ENDPOINT,
            settings.PHOENIX_PROJECT_NAME,
        )
    except Exception as exc:
        logger.warning(
            "Failed to initialize Arize Phoenix tracing (degraded gracefully): %s",
            exc,
            exc_info=True,
        )


def flush_tracing() -> None:
    """Flush pending spans and cleanly shut down the OpenTelemetry provider."""
    global _tracer_provider
    if _tracer_provider is not None:
        try:
            _tracer_provider.force_flush(timeout_millis=2000)
            _tracer_provider.shutdown()
        except Exception as exc:
            logger.warning("Error during OpenTelemetry tracer shutdown: %s", exc)
        finally:
            _tracer_provider = None


def build_run_config(
    *,
    graph: str,
    thread_id: str,
    run_name: str,
    user_id: str | None = None,
    job_id: str | None = None,
    tags: list[str] | None = None,
) -> RunnableConfig:
    """
    Construct a unified LangGraph RunnableConfig enriched with correlation,
    subject ID, and execution metadata for OpenInference tracing.

    Args:
        graph: Name of the LangGraph workflow ('pipeline', 'interview', 'reflector').
        thread_id: Checkpoint state persistence identifier.
        run_name: Human-readable trace operation name in Phoenix.
        user_id: Candidate identifier (anonymized to subject_id).
        job_id: Target job listing identifier.
        tags: Optional classification tags for Phoenix filtering.

    Returns:
        Configured RunnableConfig ready for `ainvoke`.
    """
    correlation_id = get_correlation_id() or uuid.uuid4().hex
    subject_id = derive_subject_id(user_id)

    metadata: dict[str, Any] = {
        "correlation_id": correlation_id,
        "subject_id": subject_id,
        "user_id": subject_id,
        "graph": graph,
    }
    if job_id:
        metadata["job_id"] = job_id

    tag_list = ["career-os", graph]
    if tags:
        tag_list.extend(tags)

    return {
        "configurable": {"thread_id": thread_id},
        "metadata": metadata,
        "tags": tag_list,
        "run_name": run_name,
        "recursion_limit": settings.GRAPH_RECURSION_LIMIT,
    }
