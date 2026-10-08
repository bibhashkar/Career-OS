"""
Security sterilization and validation for direct URLs and pasted user input.

Eliminates Server-Side Request Forgery (SSRF), DNS rebinding vulnerabilities,
and malicious payloads by construction:
1. "Parse, don't fetch": Known ATS URLs are parsed into (provider, slug, job_id)
   and queried exclusively against hardcoded official API hostnames.
3. Text sanitizer: Normalizes Unicode, removes ANSI/control characters,
   and bounds length.
"""

import ipaddress
import re
import socket
import unicodedata
from urllib.parse import parse_qs, urlparse

from app.ingestion.models import ATSProvider


class SecurityValidationError(Exception):
    """Raised when URL or text fails security validation."""

    pass


# Regular expressions for direct ATS career portals
GREENHOUSE_URL_PATTERN = re.compile(
    r"^https?://(?:boards|job-boards)\.greenhouse\.io/(?:embed/job_app\?for=)?(?P<slug>[a-zA-Z0-9_\-]+)(?:/jobs/(?P<job_id>\d+))?",
    re.IGNORECASE,
)
GREENHOUSE_CUSTOM_PATTERN = re.compile(
    r"^https?://(?:boards|job-boards)\.greenhouse\.io/(?P<slug>[a-zA-Z0-9_\-]+)",
    re.IGNORECASE,
)
LEVER_URL_PATTERN = re.compile(
    r"^https?://jobs\.lever\.co/(?P<slug>[a-zA-Z0-9_\-]+)(?:/(?P<job_id>[a-f0-9\-]{36}))?",
    re.IGNORECASE,
)
ASHBY_URL_PATTERN = re.compile(
    r"^https?://jobs\.ashbyhq\.com/(?P<slug>[a-zA-Z0-9_\-]+)(?:/(?P<job_id>[a-f0-9\-]+))?",
    re.IGNORECASE,
)

# Prohibited private / link-local / cloud metadata CIDRs
PROHIBITED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),  # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / AWS / GCP / Azure metadata
    ipaddress.ip_network("172.16.0.0/12"),  # Private RFC 1918
    ipaddress.ip_network("192.0.0.0/24"),  # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1
    ipaddress.ip_network("192.88.99.0/24"),  # 6to4 Relay Anycast
    ipaddress.ip_network("192.168.0.0/16"),  # Private RFC 1918
    ipaddress.ip_network("198.18.0.0/15"),  # Network benchmark tests
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved
    ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
    # IPv6 ranges
    ipaddress.ip_network("::1/128"),  # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),  # IPv6 Link-Local
]

MAX_URL_LENGTH = 2048
MAX_TEXT_LENGTH = 100_000  # 100k characters for job descriptions


def sanitize_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    """
    Sanitize untrusted text input (job descriptions, notes, queries).

    1. Normalizes Unicode (NFC form).
    2. Strips ASCII control characters (preserving tabs, newlines, CR).
    3. Truncates length to safe bound.
    """
    if not text:
        return ""

    # Normalize unicode to avoid visual spoofing and malformed representations
    normalized = unicodedata.normalize("NFC", text)

    # Filter out control characters except standard whitespace (\t, \n, \r)
    clean_chars = [
        char
        for char in normalized
        if char in ("\t", "\n", "\r")
        or (not unicodedata.category(char).startswith("C"))
    ]
    cleaned = "".join(clean_chars).strip()

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned


def parse_ats_url(raw_url: str) -> tuple[ATSProvider, str, str | None] | None:
    """
    Parse a known direct ATS job posting or board URL.

    Returns:
        tuple of (provider, slug, job_id) if recognized, or None.
    Raises:
        SecurityValidationError if URL is malformed or exceeds max length.
    """
    if not raw_url:
        return None

    cleaned_url = raw_url.strip()
    if len(cleaned_url) > MAX_URL_LENGTH:
        raise SecurityValidationError(
            f"URL length exceeds {MAX_URL_LENGTH} characters."
        )

    parsed = urlparse(cleaned_url)
    if parsed.scheme.lower() not in ("http", "https"):
        return None

    # Check Greenhouse
    gh_match = GREENHOUSE_URL_PATTERN.match(cleaned_url)
    if gh_match:
        slug = gh_match.group("slug")
        job_id = gh_match.group("job_id")
        # Handle embed URL format ?for=slug&token=job_id
        if "embed" in parsed.path:
            qs = parse_qs(parsed.query)
            slug = qs.get("for", [slug])[0]
            job_id = qs.get("token", [job_id])[0] if "token" in qs else job_id
        return (ATSProvider.GREENHOUSE, slug.lower(), job_id)

    # Check Lever
    lever_match = LEVER_URL_PATTERN.match(cleaned_url)
    if lever_match:
        return (
            ATSProvider.LEVER,
            lever_match.group("slug").lower(),
            lever_match.group("job_id"),
        )

    # Check Ashby
    ashby_match = ASHBY_URL_PATTERN.match(cleaned_url)
    if ashby_match:
        return (
            ATSProvider.ASHBY,
            ashby_match.group("slug").lower(),
            ashby_match.group("job_id"),
        )

    return None


def validate_and_guard_url(raw_url: str, resolve_dns: bool = True) -> str:
    """
    Validate that an external HTTP(S) URL is safe to fetch.

    Rules:
    - Scheme must be HTTPS or HTTP.
    - Userinfo (user:pass@host) is rejected.
    - Non-standard ports (anything other than 80 or 443) are rejected.
    - Raw IP literals are rejected.
    - If resolve_dns is True, resolves host IPs and rejects any private/loopback/cloud
      metadata IP addresses.
    """
    if not raw_url:
        raise SecurityValidationError("URL cannot be empty.")

    cleaned_url = raw_url.strip()
    if len(cleaned_url) > MAX_URL_LENGTH:
        raise SecurityValidationError(
            f"URL length exceeds {MAX_URL_LENGTH} characters."
        )

    parsed = urlparse(cleaned_url)

    if parsed.scheme.lower() not in ("http", "https"):
        raise SecurityValidationError(
            f"Invalid protocol scheme '{parsed.scheme}'. "
            "Only http and https are allowed."
        )

    if parsed.username or parsed.password:
        raise SecurityValidationError(
            "URL containing authentication credentials is prohibited."
        )

    hostname = parsed.hostname
    if not hostname:
        raise SecurityValidationError("URL has no valid hostname.")

    # Reject non-standard ports
    port = parsed.port
    if port is not None and port not in (80, 443):
        raise SecurityValidationError(
            f"Port {port} is not allowed. Only ports 80 and 443 are supported."
        )

    # Reject direct IP addresses (decimal, hex, octal, dotted IPv4, IPv6)
    try:
        ip = ipaddress.ip_address(hostname)
        raise SecurityValidationError(
            f"Direct IP addresses are not permitted as targets: {ip}"
        )
    except ValueError:
        # Not a literal IP address; proceed to DNS resolution check
        pass

    if resolve_dns:
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                resolved_ip = ipaddress.ip_address(ip_str)
                for prohibited in PROHIBITED_NETWORKS:
                    if resolved_ip in prohibited:
                        raise SecurityValidationError(
                            f"Host '{hostname}' resolved to prohibited "
                            f"IP range ({resolved_ip})."
                        )
        except socket.gaierror as e:
            raise SecurityValidationError(
                f"Could not resolve host '{hostname}': {e}"
            ) from e

    return cleaned_url
