"""
Tests for Arize Phoenix observability, OpenTelemetry tracing, and PII anonymization.

Validates:
  - Deterministic and irreversible subject ID derivation.
  - Regex PII scrubbing for candidate prompts and resumes.
  - OpenTelemetry PIIScrubbingSpanProcessor attribute sanitization.
  - Hermetic offline test isolation (Phoenix collector disabled during tests).
  - Unified RunnableConfig construction for LangGraph agent pipelines.
  - CORS header exposure for distributed correlation IDs.
  - Prometheus agent metrics and ATS loop exhaustion tracking.
"""

from unittest.mock import MagicMock

import pytest
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider

from app.agents.graph import route_ats
from app.agents.state import AgentState
from app.core.config import settings
from app.core.logging import set_correlation_id
from app.core.metrics import metrics_registry
from app.core.tracing import (
    PIIScrubbingSpanProcessor,
    build_run_config,
    derive_subject_id,
    flush_tracing,
    scrub_pii,
    setup_tracing,
)


class TestSubjectIdDerivation:
    """Test suite for deterministic, PII-free subject ID hashing."""

    def test_derive_subject_id_deterministic(self) -> None:
        """The same candidate user ID must always yield the exact same subject_id."""
        user_id = "user-12345-uuid-67890"
        id1 = derive_subject_id(user_id)
        id2 = derive_subject_id(user_id)
        assert id1 == id2
        assert id1.startswith("subj_")
        assert len(id1) == 5 + 16  # "subj_" + 16 hex chars

    def test_derive_subject_id_irreversible(self) -> None:
        """Subject ID must never leak the original user_id or email substring."""
        user_id = "candidate_john_doe_99"
        subj = derive_subject_id(user_id)
        assert "john" not in subj
        assert "doe" not in subj
        assert user_id not in subj

    def test_derive_subject_id_distinct_for_different_users(self) -> None:
        """Different candidate user IDs must produce distinct subject IDs."""
        subj_a = derive_subject_id("user_alpha")
        subj_b = derive_subject_id("user_beta")
        assert subj_a != subj_b

    def test_derive_subject_id_anonymous_fallbacks(self) -> None:
        """Empty or None user_id must cleanly map to 'subj_anonymous'."""
        assert derive_subject_id(None) == "subj_anonymous"
        assert derive_subject_id("") == "subj_anonymous"
        assert derive_subject_id("   ") == "subj_anonymous"


class TestPIIScrubbing:
    """Test suite for regex sanitization of prompt inputs and outputs."""

    def test_scrub_emails_and_phone_numbers(self) -> None:
        """Emails and phone numbers must be redacted."""
        text = "Contact me at candidate@example.com or (415) 555-0199 for scheduling."
        scrubbed = scrub_pii(text)
        assert "candidate@example.com" not in scrubbed
        assert "[EMAIL_REDACTED]" in scrubbed
        assert "(415) 555-0199" not in scrubbed
        assert "[PHONE_REDACTED]" in scrubbed

    def test_scrub_addresses(self) -> None:
        """Street addresses must be replaced with redaction tokens."""
        text = "Residing at 742 Evergreen Terrace and 100 Main Street, Apt 4B."
        scrubbed = scrub_pii(text)
        assert "742 Evergreen Terrace" not in scrubbed
        assert "100 Main Street" not in scrubbed
        assert "[ADDRESS_REDACTED]" in scrubbed

    def test_preserves_technical_keywords(self) -> None:
        """Technical skills, frameworks, and architecture terms must be untouched."""
        text = (
            "Skilled in Python, FastAPI, LangGraph, pgvector, Docker, and PostgreSQL. "
            "Evaluated with ATS threshold 75.0 on port 8000."
        )
        scrubbed = scrub_pii(text)
        assert scrubbed == text

    def test_empty_string_handling(self) -> None:
        """Empty or falsy strings must return cleanly."""
        assert scrub_pii("") == ""


class TestSpanProcessorSanitization:
    """Test suite for OpenTelemetry PIIScrubbingSpanProcessor."""

    def test_processor_scrubs_bounded_attributes(self) -> None:
        """SpanProcessor on_end must sanitize string attributes."""
        provider = TracerProvider()
        processor = PIIScrubbingSpanProcessor()
        provider.add_span_processor(processor)

        tracer = provider.get_tracer("test_tracer")
        with tracer.start_as_current_span("agent_turn") as span:
            span.set_attribute("input.prompt", "Candidate email: test@domain.org")
            span.set_attribute("agent.skill", "Python 3.12")

        # In Python OTel, after span closes, attributes can be inspected
        assert span.attributes is not None
        assert "test@domain.org" not in span.attributes["input.prompt"]
        assert "[EMAIL_REDACTED]" in span.attributes["input.prompt"]
        assert span.attributes["agent.skill"] == "Python 3.12"

    def test_processor_disabled_when_flag_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When PHOENIX_ANONYMIZE_PII is False, attributes must not be modified."""
        monkeypatch.setattr(settings, "PHOENIX_ANONYMIZE_PII", False)
        processor = PIIScrubbingSpanProcessor()

        span_mock = MagicMock(spec=ReadableSpan)
        span_mock._attributes = {"input": "email test@domain.org"}
        processor.on_end(span_mock)

        assert span_mock._attributes["input"] == "email test@domain.org"


class TestHermeticIsolationAndConfig:
    """Test suite for offline CI isolation and tracing configuration."""

    def test_is_testing_forces_phoenix_disabled(self) -> None:
        """In test environment, PHOENIX_ENABLED must resolve to False."""
        assert settings.is_testing is True
        assert settings.PHOENIX_ENABLED is False

    def test_setup_and_flush_tracing_noop_in_tests(self) -> None:
        """Tracing setup and flush must complete safely without network calls."""
        # Must execute without error
        setup_tracing()
        flush_tracing()

    def test_sampling_rate_validation(self) -> None:
        """Sampling rate must be between 0.0 and 1.0."""
        from app.core.config import Settings

        with pytest.raises(ValueError, match="PHOENIX_SAMPLING_RATE"):
            Settings(PHOENIX_SAMPLING_RATE=1.5)

        with pytest.raises(ValueError, match="PHOENIX_SAMPLING_RATE"):
            Settings(PHOENIX_SAMPLING_RATE=-0.1)


class TestRunnableConfigBuilder:
    """Test suite for build_run_config helper."""

    def test_build_run_config_metadata_and_tags(self) -> None:
        """build_run_config must construct correct metadata and tags."""
        set_correlation_id("test-corr-abc-123")
        config = build_run_config(
            graph="pipeline",
            thread_id="thread_cv_test",
            run_name="cv_tailor_run",
            user_id="user_target_99",
            job_id="job_backend_engineer",
            tags=["custom_tag"],
        )

        assert config["configurable"]["thread_id"] == "thread_cv_test"
        assert config["run_name"] == "cv_tailor_run"
        assert "metadata" in config
        metadata = config["metadata"]
        assert metadata["correlation_id"] == "test-corr-abc-123"
        assert metadata["subject_id"].startswith("subj_")
        assert metadata["user_id"] == metadata["subject_id"]
        assert metadata["graph"] == "pipeline"
        assert metadata["job_id"] == "job_backend_engineer"
        assert config["tags"] == ["career-os", "pipeline", "custom_tag"]


class TestMetricsAndLoopGuards:
    """Test suite for agent runs and ATS loop exhaustion metrics."""

    def test_record_agent_run_metrics(self) -> None:
        """record_agent_run must track execution counts and average latencies."""
        metrics_registry.record_agent_run("pipeline", "success", 1.25)
        metrics_registry.record_agent_run("pipeline", "success", 0.75)
        output = metrics_registry.generate_prometheus_output()

        assert "career_os_agent_runs_total" in output
        assert 'graph="pipeline",status="success"' in output
        assert "career_os_agent_run_duration_seconds_avg" in output
        assert 'graph="pipeline"' in output

    def test_ats_loop_exhaustion_metric(self) -> None:
        """route_ats tripping revision bounds must increment exhaustion metric."""
        state: AgentState = {
            "ats_score": 60.0,
            "revision_count": settings.MAX_REVISIONS,  # 3
        }
        decision = route_ats(state)
        assert decision == "__end__"

        updated_output = metrics_registry.generate_prometheus_output()
        assert "career_os_ats_loop_exhausted_total" in updated_output


class TestCORSExposeHeaders:
    """Test suite for CORS X-Correlation-ID exposure."""

    def test_cors_expose_headers_configured(self) -> None:
        """Settings must configure CORS_EXPOSE_HEADERS with X-Correlation-ID."""
        assert "X-Correlation-ID" in settings.CORS_EXPOSE_HEADERS
