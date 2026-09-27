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

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.cv import router as cv_router
from app.api.feedback import router as feedback_router
from app.api.interview import router as interview_router
from app.api.jobs import router as jobs_router
from app.core.config import settings
from app.core.database import engine, init_vector_extension


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application startup and teardown sequences.

    On startup: attempts to create the pgvector extension in PostgreSQL.
    The attempt is wrapped in a broad exception guard so that a cold-start
    race condition (database container not yet ready) does not crash the
    server process — the extension will be created on the next successful
    restart or migration run instead.

    On shutdown: disposes the SQLAlchemy async engine, which closes all
    pooled psycopg connections gracefully before the process exits.
    """
    try:
        await init_vector_extension()
    except Exception:
        # Database may still be starting up in Docker; proceed without blocking.
        pass
    yield
    # Release all connections back to the OS on graceful shutdown.
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Stateful Career Operating System API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS is configured for the decoupled Vite + React frontend.
# The frontend is a pure presentation layer — it has no business logic and
# communicates exclusively through this API. Wildcard methods and headers are
# intentionally permissive for local development; tighten in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers. Each router is a thin transport adapter — no business
# logic lives here; routers delegate directly to compiled LangGraph graphs.
app.include_router(jobs_router)
app.include_router(cv_router)
app.include_router(feedback_router)
app.include_router(interview_router)


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
