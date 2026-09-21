"""Main FastAPI application entry point with CORS and healthcheck endpoints."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, init_vector_extension


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycles."""
    # Attempt vector extension bootstrap if database is reachable
    try:
        await init_vector_extension()
    except Exception:
        # Avoid crashing startup if database container is still starting up
        pass
    yield
    # Dispose of engine connection pool on shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Stateful Career Operating System API",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for decoupled React frontend presentation layer
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Health check endpoint validating service status and database connectivity."""
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
