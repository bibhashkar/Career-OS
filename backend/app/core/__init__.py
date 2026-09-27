"""
Core infrastructure: configuration, database engine, and session management.

Provides the application-wide SQLAlchemy async engine, session factory, and
Pydantic settings singleton. Everything in this package is shared infrastructure
consumed by the API layer and the agent tools — nothing in ``core`` depends on
agent or API code.
"""
