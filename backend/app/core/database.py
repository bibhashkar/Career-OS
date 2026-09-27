"""
SQLAlchemy async engine, session factory, and pgvector extension bootstrap.

This module owns all database connectivity infrastructure for the application.
All other modules consume the ``engine`` and ``async_session_maker`` exported
here rather than creating their own connections, ensuring the connection pool
is shared globally and bounded by the configured pool_size.

Connection pool sizing rationale:
  pool_size=10  – Maximum concurrent long-lived connections held open.
  max_overflow=20 – Additional short-lived connections allowed under burst load.
  Total ceiling: 30 connections before psycopg raises OperationalError.
  This headroom is intentional for an async server handling concurrent requests
  across the agent pipeline and WebSocket sessions simultaneously.

pool_pre_ping=True ensures stale connections are discarded before use, which
prevents mysterious ``SSL connection has been closed unexpectedly`` errors when
the database container is restarted without restarting the application server.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Application-wide async engine. ``echo=APP_DEBUG`` prints all SQL to stdout in
# development — useful for understanding ORM-generated queries, but must be
# disabled in production to avoid leaking query structure into logs.
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory shared by all request handlers.
# expire_on_commit=False keeps ORM objects usable after the session commits,
# which matters for async code where the session may be closed before the
# response serialiser accesses the returned model attributes.
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session for use as a FastAPI dependency.

    Usage in a route::

        async def my_route(db: AsyncSession = Depends(get_db)) -> ...

    The session commits on successful exit and rolls back on any unhandled
    exception, then is returned to the connection pool automatically.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async session for standalone use outside of request scope.

    Use this when you need a database session in background tasks, agent node
    tools, or test fixtures where the FastAPI dependency injector is not active.
    Semantics are identical to ``get_db`` — commits on clean exit, rolls back
    on exception — but exposed as an async context manager rather than a
    generator dependency.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_vector_extension() -> None:
    """
    Create the pgvector extension in PostgreSQL if it does not already exist.

    pgvector is a PostgreSQL extension that adds a ``vector`` column type and
    approximate nearest-neighbour index operators (ivfflat, hnsw). It must be
    installed once per database before the ``cv_block.embedding`` column can be
    created or queried. ``CREATE EXTENSION IF NOT EXISTS`` is idempotent, so
    this function is safe to call on every startup.

    This call is skipped for non-PostgreSQL URLs (e.g. SQLite in unit tests)
    to avoid driver errors when the extension concept does not apply.
    """
    if "postgresql" in settings.DATABASE_URL:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
