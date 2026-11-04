"""
Deterministic content hashing and fingerprinting for jobs, experiences, and candidate proof points.
"""

import hashlib

from app.domain.regex_patterns import (
    RE_BULLET_PREFIX,
    RE_CALENDAR_YEAR,
    RE_CORP_SUFFIX,
    RE_JOB_TITLE_GEO_DASH,
    RE_JOB_TITLE_GEO_PARENS,
    RE_NON_ALPHANUMERIC,
    RE_WHITESPACE,
)


def normalize_alphanumeric(text: str | None) -> str:
    """Lowercase text and strip all non-alphanumeric characters."""
    if not text:
        return ""
    return RE_NON_ALPHANUMERIC.sub("", text.lower())


def sha256_prefix(text: str, length: int = 32) -> str:
    """Compute SHA-256 hash digest truncated to the given length."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def compute_content_hash(description: str) -> str:
    """Compute SHA-256 hash of job description text for change tracking."""
    return sha256_prefix(description, length=32)


def normalize_job_title(title: str) -> str:
    """
    Normalize job title by lowercasing and stripping trailing geographic markers
    and parentheses, followed by alphanumeric normalization.
    """
    t = title.lower().strip()
    t = RE_JOB_TITLE_GEO_DASH.sub("", t)
    t = RE_JOB_TITLE_GEO_PARENS.sub("", t)
    return normalize_alphanumeric(t)


def compute_dedupe_fingerprint(company: str, title: str, location: str) -> str:
    """
    Compute cross-source dedupe fingerprint:
    hash(normalized company, normalized title, normalized location region).
    """
    norm_company = normalize_alphanumeric(company)
    norm_title = normalize_alphanumeric(title)
    norm_loc = normalize_alphanumeric(location)
    raw = f"{norm_company}:{norm_title}:{norm_loc}"
    return sha256_prefix(raw, length=32)


def compute_canonical_fingerprint(company: str, title: str) -> str:
    """Compute canonical requisition fingerprint invariant to geographic variants."""
    norm_company = normalize_alphanumeric(company)
    norm_title = normalize_job_title(title)
    raw = f"{norm_company}:{norm_title}"
    return sha256_prefix(raw, length=32)


def compute_bullet_fingerprint(user_id: str | None, org: str | None, text: str) -> str:
    """Compute deterministic unique content fingerprint for a career achievement bullet."""
    norm_user = str(user_id or "").strip().lower()
    norm_org = normalize_alphanumeric(str(org or ""))
    clean_text = RE_BULLET_PREFIX.sub("", text.strip())
    norm_content = RE_WHITESPACE.sub(" ", clean_text.lower()).strip()
    raw = f"{norm_user}:{norm_org}:{norm_content}"
    return sha256_prefix(raw, length=32)


def compute_tenure_fingerprint(company: str, title: str, start_year: str) -> str:
    """Compute deterministic unique fingerprint for an employment tenure."""
    norm_company = normalize_alphanumeric(company)
    norm_company = RE_CORP_SUFFIX.sub("", norm_company)
    norm_title = normalize_alphanumeric(title)
    match_year = RE_CALENDAR_YEAR.search(str(start_year))
    norm_year = match_year.group(1) if match_year else "any"
    raw = f"{norm_company}:{norm_title}:{norm_year}"
    return sha256_prefix(raw, length=32)
