"""
Unit tests for security sterilization and URL validation (SSRF / malicious input).
"""

import pytest

from app.ingestion.models import ATSProvider
from app.ingestion.security import (
    SecurityValidationError,
    parse_ats_url,
    sanitize_text,
    validate_and_guard_url,
)


def test_sanitize_text_normalizes_and_strips_control_characters() -> None:
    raw = "Senior Software\tEngineer\n\x00\x08\x0b at Google \r"
    cleaned = sanitize_text(raw)
    assert "\x00" not in cleaned
    assert "\x08" not in cleaned
    assert "Senior Software\tEngineer\n at Google" in cleaned
    assert "\t" in cleaned
    assert "\n" in cleaned


def test_sanitize_text_truncates_oversized_text() -> None:
    huge = "a" * 200
    cleaned = sanitize_text(huge, max_length=50)
    assert len(cleaned) == 50


def test_parse_ats_url_greenhouse() -> None:
    url = "https://boards.greenhouse.io/stripe/jobs/1234567"
    result = parse_ats_url(url)
    assert result == (ATSProvider.GREENHOUSE, "stripe", "1234567")

    board_only = "https://boards.greenhouse.io/stripe"
    assert parse_ats_url(board_only) == (ATSProvider.GREENHOUSE, "stripe", None)

    embed_url = "https://boards.greenhouse.io/embed/job_app?for=figma&token=98765"
    assert parse_ats_url(embed_url) == (ATSProvider.GREENHOUSE, "figma", "98765")


def test_parse_ats_url_lever() -> None:
    lever_url = "https://jobs.lever.co/postman/a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
    result = parse_ats_url(lever_url)
    assert result == (
        ATSProvider.LEVER,
        "postman",
        "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    )

    board_only = "https://jobs.lever.co/postman"
    assert parse_ats_url(board_only) == (ATSProvider.LEVER, "postman", None)


def test_parse_ats_url_ashby() -> None:
    ashby_url = "https://jobs.ashbyhq.com/linear/4567-abc-890"
    result = parse_ats_url(ashby_url)
    assert result == (ATSProvider.ASHBY, "linear", "4567-abc-890")

    board_only = "https://jobs.ashbyhq.com/linear"
    assert parse_ats_url(board_only) == (ATSProvider.ASHBY, "linear", None)


def test_parse_ats_url_unrecognized() -> None:
    assert parse_ats_url("https://careers.google.com/jobs/results/123") is None
    assert parse_ats_url("https://linkedin.com/jobs/view/123") is None


def test_validate_and_guard_url_blocks_credentials() -> None:
    with pytest.raises(SecurityValidationError, match="credentials"):
        validate_and_guard_url("https://admin:secret@malicious.com", resolve_dns=False)


def test_validate_and_guard_url_blocks_non_standard_ports() -> None:
    with pytest.raises(SecurityValidationError, match="Port 8080 is not allowed"):
        validate_and_guard_url("https://example.com:8080/careers", resolve_dns=False)


def test_validate_and_guard_url_blocks_direct_ip_literals() -> None:
    # IPv4 loopback
    with pytest.raises(SecurityValidationError, match="Direct IP"):
        validate_and_guard_url("http://127.0.0.1/jobs", resolve_dns=False)

    # Cloud metadata IP literal
    with pytest.raises(SecurityValidationError, match="Direct IP"):
        validate_and_guard_url(
            "http://169.254.169.254/latest/meta-data", resolve_dns=False
        )

    # IPv6 loopback
    with pytest.raises(SecurityValidationError, match="Direct IP"):
        validate_and_guard_url("http://[::1]/internal", resolve_dns=False)


def test_validate_and_guard_url_blocks_disallowed_schemes() -> None:
    with pytest.raises(SecurityValidationError, match="Invalid protocol scheme"):
        validate_and_guard_url("ftp://example.com/file", resolve_dns=False)
    with pytest.raises(SecurityValidationError, match="Invalid protocol scheme"):
        validate_and_guard_url("file:///etc/passwd", resolve_dns=False)


def test_validate_and_guard_url_resolves_and_blocks_loopback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Mock socket.getaddrinfo to simulate evil domain resolving to 127.0.0.1
    def mock_getaddrinfo(host: str, port: int | None) -> list[tuple]:
        return [(2, 1, 6, "", ("127.0.0.1", 80))]

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)

    with pytest.raises(SecurityValidationError, match="prohibited IP range"):
        validate_and_guard_url(
            "https://evil-rebind.internal.com/test", resolve_dns=True
        )


def test_validate_and_guard_url_resolves_and_blocks_cloud_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Mock socket.getaddrinfo to simulate cloud metadata DNS resolution
    def mock_getaddrinfo(host: str, port: int | None) -> list[tuple]:
        return [(2, 1, 6, "", ("169.254.169.254", 80))]

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)

    with pytest.raises(SecurityValidationError, match="prohibited IP range"):
        validate_and_guard_url("https://metadata.evil.com/test", resolve_dns=True)


def test_validate_and_guard_url_allows_legitimate_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Mock socket.getaddrinfo to simulate public IP
    def mock_getaddrinfo(host: str, port: int | None) -> list[tuple]:
        return [(2, 1, 6, "", ("93.184.216.34", 443))]

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)

    safe_url = "https://example.com/careers"
    assert validate_and_guard_url(safe_url, resolve_dns=True) == safe_url
