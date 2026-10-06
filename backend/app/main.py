"""
Career-OS FastAPI application entry point.

This module assembles the full FastAPI application: registers CORS middleware,
mounts all API routers, and wires up the application lifespan handler that
initialises the pgvector database extension on startup and disposes of the
connection pool on shutdown.

Why a lifespan context manager instead of @app.on_event?
FastAPI deprecated on_event handlers in favour of the asynccontextmanager
lifecycle pattern (PEP 343) because it keeps startup and shutdown logic
co-located and makes the dependency graph explicit. The vector extension
initialisation is placed here — not inside a router or model module — to ensure
it runs exactly once before any request is processed.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.agents.graph import close_postgres_saver, init_postgres_saver
from app.api.applications import router as applications_router
from app.api.cv import router as cv_router
from app.api.feedback import router as feedback_router
from app.api.interview import router as interview_router
from app.api.jobs import router as jobs_router
from app.core.config import settings
from app.core.database import engine, init_vector_extension
from app.core.errors import setup_exception_handlers
from app.core.logging import CorrelationIdMiddleware, setup_logging
from app.core.metrics import PrometheusMetricsMiddleware, metrics_registry
from app.core.rate_limit import RateLimitMiddleware
from app.core.security import SecurityHeadersMiddleware

logger = logging.getLogger("career_os.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application startup and teardown sequences.

    On startup:
      - Attempts to create the pgvector extension in PostgreSQL.
      - In non-test environments, initializes AsyncPostgresSaver for persistent
        LangGraph checkpointing across server restarts.

    On shutdown:
      - Closes the AsyncPostgresSaver connection pool.
      - Disposes the SQLAlchemy async engine, closing all pooled psycopg
        connections gracefully before process exit.
    """
    setup_logging()
    try:
        await init_vector_extension()
    except Exception as exc:
        # Database may still be starting up in Docker; proceed with logged warning.
        logger.warning(f"Vector extension bootstrap deferred during startup: {exc}")

    if settings.APP_ENV != "test":
        await init_postgres_saver()

    yield

    await close_postgres_saver()
    # Release all connections back to the OS on graceful shutdown.
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Stateful Career Operating System API",
    version="0.1.0",
    lifespan=lifespan,
)

# RFC 7807 Problem Details exception handlers for uniform error serialization
setup_exception_handlers(app)

# Prometheus metrics tracking middleware
app.add_middleware(PrometheusMetricsMiddleware)

# Rate limiting middleware protecting resource-intensive agent workloads
app.add_middleware(RateLimitMiddleware)

# Security headers middleware enforcing OWASP protection policies
app.add_middleware(SecurityHeadersMiddleware)

# Distributed correlation ID middleware for request tracing and timing
app.add_middleware(CorrelationIdMiddleware)

# CORS is configured for the decoupled Vite + React frontend.
# Explicit allowed methods and headers prevent arbitrary verb and header abuse.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Mount API routers. Each router is a thin transport adapter — no business
# logic lives here; routers delegate directly to compiled LangGraph graphs.
app.include_router(jobs_router)
app.include_router(cv_router)
app.include_router(applications_router)
app.include_router(feedback_router)
app.include_router(interview_router)


@app.get("/metrics", response_class=Response)
async def metrics_endpoint() -> Response:
    """
    Export Prometheus text format application and connection pool metrics.
    """
    content = metrics_registry.generate_prometheus_output()
    return Response(
        content=content, media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """
    Return service health and database connectivity status.

    Executes a lightweight ``SELECT 1`` probe against the live connection pool.
    Used by Docker health-checks, Kubernetes readiness probes, and monitoring
    dashboards. Returns ``database: unreachable`` instead of a 5xx so that
    load balancers can drain traffic gracefully during database failovers.
    """
    db_status = "healthy"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
    except Exception:
        db_status = "unreachable"

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": db_status,
    }
