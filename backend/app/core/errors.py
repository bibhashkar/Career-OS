"""
RFC 7807 Problem Details global exception handling.

Why RFC 7807?
Standard HTTP error responses often vary across endpoints, returning ad-hoc
dicts like ``{"error": "message"}`` or ``{"detail": "..."}``. The IETF RFC 7807
specification defines a standardized ``application/problem+json`` media type
that guarantees predictable error schemas across all API surfaces.

Security Benefits:
  - Prevents internal information leakage: Unhandled exceptions (database query
    errors, connection timeouts) are caught at the application boundary and
    sanitized. The client receives a safe error description and a correlation ID
    rather than a raw Python stack trace or SQL syntax error.
  - Correlation Tracing: Every problem response includes the active
    ``correlation_id`` from ``app.core.logging`` so operators can cross-reference
    production logs instantly without requiring user PII.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_correlation_id

logger = logging.getLogger("career_os.errors")


def create_problem_response(
    status_code: int,
    title: str,
    detail: str,
    instance: str,
    type_uri: str = "about:blank",
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    """
    Construct an RFC 7807 compliant problem details JSONResponse.

    Args:
        status_code: HTTP status code.
        title: Short, human-readable summary of the problem type.
        detail: Human-readable explanation specific to this occurrence.
        instance: URI reference identifying the specific request endpoint.
        type_uri: URI reference identifying the problem type.
        extra: Optional additional diagnostic attributes (e.g. invalid_params).

    Returns:
        JSONResponse with media_type application/problem+json.
    """
    problem: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
        "correlation_id": get_correlation_id() or None,
    }

    if extra:
        problem.update(extra)

    return JSONResponse(
        status_code=status_code,
        content=problem,
        media_type="application/problem+json",
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle explicit HTTPExceptions (e.g. 404, 403, 400)."""
    title = (
        "Not Found" if exc.status_code == status.HTTP_404_NOT_FOUND else "HTTP Error"
    )
    return create_problem_response(
        status_code=exc.status_code,
        title=title,
        detail=str(exc.detail),
        instance=request.url.path,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic request validation failures (HTTP 422)."""
    sanitized_errors = [
        {
            "loc": [str(x) for x in err.get("loc", [])],
            "msg": err.get("msg", "Invalid parameter"),
            "type": err.get("type", "value_error"),
        }
        for err in exc.errors()
    ]

    return create_problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        title="Unprocessable Entity",
        detail="Request body or query parameter validation failed.",
        instance=request.url.path,
        extra={"invalid_params": sanitized_errors},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected internal exceptions (HTTP 500).

    Logs full traceback internally with correlation ID, but shields client
    from internal implementation details.
    """
    cid = get_correlation_id() or "unknown"
    logger.exception(
        f"Unhandled exception on {request.method} {request.url.path} "
        f"[correlation_id={cid}]: {exc}"
    )

    return create_problem_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail=(
            f"An unexpected internal error occurred. Please contact support "
            f"referencing correlation ID: {cid}"
        ),
        instance=request.url.path,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register RFC 7807 exception handlers on the FastAPI application."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, unhandled_exception_handler)
