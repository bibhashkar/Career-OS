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
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine
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


@event.listens_for(Session, "after_flush")
def audit_orm_flush(session: Session, flush_context: Any) -> None:
    """
    OpenTelemetry event listener auditing database mutations.
    Attaches modified table names and dirty columns to the active span.
    """
    span = trace.get_current_span()
    if not span.is_recording():
        return

    dirty_tables: set[str] = set()
    modified_cols: list[str] = []

    for obj in session.dirty:
        table_name = getattr(obj, "__tablename__", type(obj).__name__)
        dirty_tables.add(table_name)
        try:
            state = inspect(obj)
            if state is not None:
                for attr in state.attrs:
                    hist = attr.history
                    if hist.has_changes():
                        modified_cols.append(f"{table_name}.{attr.key}")
        except Exception:
            pass

    for obj in session.new:
        table_name = getattr(obj, "__tablename__", type(obj).__name__)
        dirty_tables.add(table_name)
        modified_cols.append(f"{table_name}.* (insert)")

    if dirty_tables:
        span.set_attribute("db.orm.modified_tables", list(dirty_tables))
    if modified_cols:
        span.set_attribute("db.orm.modified_columns", modified_cols[:50])


def setup_tracing(app: Any | None = None) -> None:
    """
    Initialize OpenTelemetry TracerProvider with Phoenix & OTLP HTTP exporters,
    FastAPI, SQLAlchemy, HTTPX, and OpenInference LangChain instrumentation.

    Safely degrades if tracing is disabled, in test environments, or if
    the collector endpoints are unreachable.
    """
    global _tracer_provider, _instrumented
    if (
        not settings.PHOENIX_ENABLED and not settings.OTEL_ENABLED
    ) or settings.is_testing:
        logger.info(
            "Tracing disabled [phoenix=%s, otel=%s, is_testing=%s]",
            settings.PHOENIX_ENABLED,
            settings.OTEL_ENABLED,
            settings.is_testing,
        )
        return

    if _instrumented:
        return

    try:
        sampler = TraceIdRatioBased(settings.PHOENIX_SAMPLING_RATE)
        provider = TracerProvider(sampler=sampler)
        provider.add_span_processor(PIIScrubbingSpanProcessor())

        if settings.PHOENIX_ENABLED and settings.PHOENIX_COLLECTOR_ENDPOINT:
            phoenix_exporter = OTLPSpanExporter(
                endpoint=settings.PHOENIX_COLLECTOR_ENDPOINT,
                timeout=2,
            )
            provider.add_span_processor(
                BatchSpanProcessor(
                    phoenix_exporter,
                    max_queue_size=2048,
                    export_timeout_millis=2000,
                    schedule_delay_millis=5000,
                )
            )

        if settings.OTEL_ENABLED and settings.OTEL_EXPORTER_OTLP_ENDPOINT:
            otel_exporter = OTLPSpanExporter(
                endpoint=f"{settings.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces",
                timeout=2,
            )
            provider.add_span_processor(
                BatchSpanProcessor(
                    otel_exporter,
                    max_queue_size=2048,
                    export_timeout_millis=2000,
                    schedule_delay_millis=5000,
                )
            )

        trace.set_tracer_provider(provider)
        LangChainInstrumentor().instrument(tracer_provider=provider)
        SQLAlchemyInstrumentor().instrument(
            engine=engine.sync_engine,
            tracer_provider=provider,
        )
        HTTPXClientInstrumentor().instrument(tracer_provider=provider)
        LoggingInstrumentor().instrument(
            tracer_provider=provider,
            set_logging_format=False,
        )
        if app is not None:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=provider,
                excluded_urls="metrics,health",
            )

        _tracer_provider = provider
        _instrumented = True
        logger.info(
            "360° OpenTelemetry & Arize Phoenix tracing initialized [otel=%s, phoenix=%s]",
            settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            settings.PHOENIX_COLLECTOR_ENDPOINT,
        )
    except Exception as exc:
        logger.warning(
            "Failed to initialize tracing (degraded gracefully): %s",
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
