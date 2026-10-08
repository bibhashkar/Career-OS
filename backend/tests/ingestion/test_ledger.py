"""
Tests for persistent rate-limit ledger and circuit breaker.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.ledger import CircuitBreaker, PersistentBudgetLedger
from app.models.ingestion import ProviderState


@pytest.mark.asyncio
async def test_budget_ledger_acquire_and_quota_exhaustion(
    db_session: AsyncSession,
) -> None:
    ledger = PersistentBudgetLedger(db_session)
    provider = "jobspy"  # limit is 30 hourly

    # Acquire permits up to 30
    assert await ledger.acquire_permit(provider, cost=20) is True
    assert await ledger.acquire_permit(provider, cost=10) is True

    # Next permit should be rejected
    assert await ledger.acquire_permit(provider, cost=1) is False

    usage = await ledger.get_usage(provider)
    assert usage["current_calls"] == 30
    assert usage["is_exhausted"] is True
    assert usage["remaining"] == 0


@pytest.mark.asyncio
async def test_circuit_breaker_trips_and_recovers(db_session: AsyncSession) -> None:
    breaker = CircuitBreaker(db_session, failure_threshold=3, cooldown_seconds=2)
    provider = "greenhouse"

    # Initially available
    assert await breaker.is_available(provider) is True

    # Record 2 failures (below threshold 3)
    await breaker.record_failure(provider, "500 Server Error")
    await breaker.record_failure(provider, "502 Bad Gateway")
    assert await breaker.is_available(provider) is True

    # 3rd failure trips the breaker
    await breaker.record_failure(provider, "503 Service Unavailable")
    assert await breaker.is_available(provider) is False

    # Simulate passage of cooldown time
    stmt = select(ProviderState).where(ProviderState.provider == provider)
    state = (await db_session.execute(stmt)).scalar_one()
    state.cooldown_until = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.flush()

    # Half-open probe should be allowed
    assert await breaker.is_available(provider) is True

    # Record success resets breaker state
    await breaker.record_success(provider)
    assert await breaker.is_available(provider) is True
    assert state.failure_count == 0
    assert state.is_circuit_open is False
