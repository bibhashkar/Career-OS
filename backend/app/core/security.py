"""
HTTP Security headers middleware and hardening policies.

Why HTTP Security Headers?
Web applications are vulnerable to clickjacking, MIME-type sniffing, cross-site
scripting (XSS), and unauthorized browser feature delegation unless the server
instructs the browser on permissible security boundaries via HTTP response headers.

This module provides a production-grade ``SecurityHeadersMiddleware`` that injects:
  - ``X-Content-Type-Options: nosniff`` — Prevents browsers from MIME-sniffing
    responses away from the declared content-type, blocking script injection.
  - ``X-Frame-Options: DENY`` — Completely prevents the application from being
    embedded inside an <iframe>, frame, or object, preventing clickjacking attacks.
  - ``Referrer-Policy: strict-origin-when-cross-origin`` — Protects candidate privacy
    by restricting referrer leakage on cross-origin requests while preserving origins.
  - ``Permissions-Policy: geolocation=(), microphone=(), camera=()`` — Disables
    browser hardware access APIs within the web application scope.
  - ``X-XSS-Protection: 0`` — Disables legacy, buggy XSS auditors in older browsers
    in accordance with modern OWASP recommendations.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Inject OWASP-recommended HTTP security headers into every outgoing response.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the HTTP request and attach hardened security headers to the response.
        """
        response: Response = await call_next(request)

        # Prevent browsers from MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking by disallowing framing
        response.headers["X-Frame-Options"] = "DENY"

        # Mitigate referrer information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict hardware permissions
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Disable buggy legacy XSS filter
        response.headers["X-XSS-Protection"] = "0"

        return response
