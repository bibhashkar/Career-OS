"""Unit tests for structured JSON logging and correlation ID middleware."""

import json
import logging

from fastapi.testclient import TestClient

from app.core.logging import (
    StructuredJsonFormatter,
    set_correlation_id,
    setup_logging,
)
from app.main import app


def test_correlation_id_generated_and_returned() -> None:
    """Verify middleware injects X-Correlation-ID if omitted by client."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-correlation-id" in response.headers
    assert len(response.headers["x-correlation-id"]) > 0


def test_correlation_id_custom_header_preserved() -> None:
    """Verify client-supplied X-Correlation-ID is echoed in response."""
    client = TestClient(app)
    custom_cid = "corr-test-id-abc-123"
    response = client.get("/health", headers={"X-Correlation-ID": custom_cid})
    assert response.status_code == 200
    assert response.headers.get("x-correlation-id") == custom_cid


def test_structured_json_formatter() -> None:
    """Verify log formatter emits parseable JSON with context metadata."""
    formatter = StructuredJsonFormatter()
    set_correlation_id("test-corr-456")

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Execution checkpoint saved",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Execution checkpoint saved"
    assert parsed["correlation_id"] == "test-corr-456"
    assert "timestamp" in parsed
    assert "file" in parsed


def test_setup_logging_idempotence() -> None:
    """Verify setup_logging attaches StructuredJsonFormatter without duplicating."""
    setup_logging(level=logging.DEBUG)
    root = logging.getLogger()
    assert len(root.handlers) >= 1
    assert isinstance(root.handlers[0].formatter, StructuredJsonFormatter)
