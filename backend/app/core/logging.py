"""
Structured JSON logging and distributed correlation ID propagation.

Why structured logging?
Standard unstructured log strings are difficult to query, filter, and alert on
in production log aggregators (e.g., Datadog, CloudWatch, Google Cloud Logging).
This module configures JSON-formatted log output containing consistent metadata:
timestamp, log level, logger name, module path, and active correlation ID.

Why correlation IDs?
Career-OS processes multi-step agent workflows across REST calls, WebSocket frames,
and database transactions. When an error occurs, an ``X-Correlation-ID`` enables
engineers to trace the exact lifecycle of an execution thread without logging
sensitive user personally identifiable information (PII).
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any

from fastapi import Request, Response
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Context variable storing active request correlation ID across async task boundaries
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")
# Context variable storing active client action tag (e.g. "Dashboard.TailorCVButton")
client_action_ctx: ContextVar[str] = ContextVar("client_action", default="")


def get_correlation_id() -> str:
    """Retrieve the current task's correlation ID or empty string if unset."""
    return correlation_id_ctx.get()


def set_correlation_id(cid: str) -> None:
    """Set the correlation ID for the current async task context."""
    correlation_id_ctx.set(cid)


def get_client_action() -> str:
    """Retrieve the current task's client UI action tag or empty string if unset."""
    return client_action_ctx.get()


def set_client_action(action: str) -> None:
    """Set the client UI action tag for the current async task context."""
    client_action_ctx.set(action)


def get_current_trace_id() -> str | None:
    """Retrieve the 32-character hexadecimal trace ID from the active OpenTelemetry span."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        return format(ctx.trace_id, "032x")
    return None


class StructuredJsonFormatter(logging.Formatter):
    """
    Format standard library log records as structured single-line JSON.

    Sanitizes log records to guarantee that sensitive PII (passwords, tokens,
    resumes) is not accidentally leaked into centralized monitoring streams.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Serialize log record attributes to JSON string."""
        log_payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id() or None,
            "trace_id": get_current_trace_id(),
            "client_action": get_client_action() or None,
            "file": f"{record.filename}:{record.lineno}",
        }

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure application-wide root logger with StructuredJsonFormatter.

    Idempotent: Replaces default StreamHandler so that all uvicorn, fastapi,
    and application logs emit uniform JSON.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called repeatedly
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to extract or inject X-Correlation-ID and log HTTP timing.

    1. Inspects incoming request headers for ``X-Correlation-ID``; generates a
       fresh UUID if absent.
    2. Stores the identifier in ``correlation_id_ctx`` context variable.
    3. Measures and logs request execution latency.
    4. Attaches ``X-Correlation-ID`` to the outgoing response headers.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process incoming request, track latency, and attach correlation header."""
        correlation_id = request.headers.get("X-Correlation-ID") or uuid.uuid4().hex
        set_correlation_id(correlation_id)

        client_action = request.headers.get("X-Client-Action", "").strip()
        set_client_action(client_action)

        start_time = time.monotonic()
        logger = logging.getLogger("career_os.http")

        try:
            response = await call_next(request)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            response.headers["X-Correlation-ID"] = correlation_id

            trace_id = get_current_trace_id()
            if trace_id:
                response.headers["X-Trace-ID"] = trace_id
            if client_action:
                response.headers["X-Client-Action"] = client_action

            logger.info(
                f"{request.method} {request.url.path} "
                f"status={response.status_code} duration_ms={duration_ms}"
            )
            return response
        except Exception:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.exception(
                f"Unhandled exception in {request.method} {request.url.path} "
                f"after {duration_ms}ms"
            )
            raise
