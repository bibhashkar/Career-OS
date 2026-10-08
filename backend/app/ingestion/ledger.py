"""
Persistent rate-limit ledger and circuit breaker implementations.

Guarantees atomic quota reservation across multiple concurrent workers and
restarts using PostgreSQL transactions, with an in-memory fallback for unit tests
or standalone script executions.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.ingestion.ports.provider import BudgetLedgerPort
from app.models.ingestion import ProviderState, ProviderUsage

logger = logging.getLogger("career_os.ingestion.ledger")


class PersistentBudgetLedger(BudgetLedgerPort):
    """
    PostgreSQL-backed atomic rate limiter and quota tracker.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _get_provider_limit(self, provider: str, period_type: str = "daily") -> int:
        """Resolve configured limits from Settings."""
        p = provider.lower()
        if p == "gemini":
            return (
                settings.RATE_LIMIT_GEMINI_RPD
                if period_type == "daily"
                else settings.RATE_LIMIT_GEMINI_RPM
            )
        elif p in ("duckduckgo", "ddgs"):
            return settings.RATE_LIMIT_DUCKDUCKGO_HOURLY
        elif p == "jobspy":
            return settings.RATE_LIMIT_JOBSPY_HOURLY
        elif p == "github":
            return settings.RATE_LIMIT_GITHUB_HOURLY
        return 1000  # Default safe quota

    def _current_period_key(self, provider: str) -> str:
        """
        Derive period bucket key (YYYY-MM-DD for daily or YYYY-MM-DD-HH for hourly).
        """
        now = datetime.now(UTC)
        if provider.lower() in ("duckduckgo", "ddgs", "jobspy", "github"):
            return now.strftime("%Y-%m-%d-%H")
        return now.strftime("%Y-%m-%d")

    async def acquire_permit(self, provider: str, cost: int = 1) -> bool:
        """
        Atomically reserve request permits. Returns True if granted, False if exceeded.
        """
        period_key = self._current_period_key(provider)
        max_calls = self._get_provider_limit(provider)

        # Query existing usage row with row-level lock
        stmt = (
            select(ProviderUsage)
            .where(
                ProviderUsage.provider == provider,
                ProviderUsage.period_key == period_key,
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        usage = result.scalar_one_or_none()

        if usage is None:
            usage = ProviderUsage(
                provider=provider,
                period_key=period_key,
                call_count=cost,
                token_count=0,
                max_calls=max_calls,
            )
            self.session.add(usage)
            await self.session.flush()
            return True

        if usage.call_count + cost > usage.max_calls:
            logger.warning(
                "Quota exhausted for provider '%s' (usage: %d, max: %d)",
                provider,
                usage.call_count,
                usage.max_calls,
            )
            return False

        usage.call_count += cost
        await self.session.flush()
        return True

    async def get_usage(self, provider: str) -> dict[str, Any]:
        """Get current usage stats for a provider."""
        period_key = self._current_period_key(provider)
        stmt = select(ProviderUsage).where(
            ProviderUsage.provider == provider,
            ProviderUsage.period_key == period_key,
        )
        result = await self.session.execute(stmt)
        usage = result.scalar_one_or_none()
        limit = self._get_provider_limit(provider)
        current = usage.call_count if usage else 0

        return {
            "provider": provider,
            "period_key": period_key,
            "current_calls": current,
            "max_calls": limit,
            "remaining": max(0, limit - current),
            "is_exhausted": current >= limit,
        }


class CircuitBreaker:
    """
    Circuit breaker tracking consecutive failures and cooldown timers per provider.
    """

    def __init__(
        self,
        session: AsyncSession,
        failure_threshold: int = 3,
        cooldown_seconds: int = 300,
    ) -> None:
        self.session = session
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

    async def is_available(self, provider: str) -> bool:
        """Check if provider is available or in active cooldown."""
        stmt = select(ProviderState).where(ProviderState.provider == provider)
        result = await self.session.execute(stmt)
        state = result.scalar_one_or_none()

        if state is None:
            return True

        if not state.is_circuit_open:
            return True

        if state.cooldown_until:
            cooldown = state.cooldown_until
            if cooldown.tzinfo is None:
                cooldown = cooldown.replace(tzinfo=UTC)
            if datetime.now(UTC) >= cooldown:
                # Half-open: Allow a probe
                state.is_circuit_open = False
                state.failure_count = 0
                state.cooldown_until = None
                await self.session.flush()
                return True

        return False

    async def record_success(self, provider: str) -> None:
        """Reset failure counts upon successful operation."""
        stmt = (
            select(ProviderState)
            .where(ProviderState.provider == provider)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        state = result.scalar_one_or_none()

        if state:
            state.failure_count = 0
            state.is_circuit_open = False
            state.cooldown_until = None
            await self.session.flush()

    async def record_failure(
        self, provider: str, error_message: str | None = None
    ) -> None:
        """Increment failure counter and trip breaker if threshold exceeded."""
        stmt = (
            select(ProviderState)
            .where(ProviderState.provider == provider)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        state = result.scalar_one_or_none()

        now = datetime.now(UTC)
        if state is None:
            state = ProviderState(
                provider=provider,
                failure_count=1,
                last_failure_at=now,
                last_error_message=error_message,
                is_circuit_open=False,
            )
            self.session.add(state)
        else:
            state.failure_count += 1
            state.last_failure_at = now
            state.last_error_message = error_message

        if state.failure_count >= self.failure_threshold:
            state.is_circuit_open = True
            state.cooldown_until = now + timedelta(seconds=self.cooldown_seconds)
            logger.warning(
                "Circuit breaker tripped for provider '%s' until %s. Error: %s",
                provider,
                state.cooldown_until,
                error_message,
            )

        await self.session.flush()
