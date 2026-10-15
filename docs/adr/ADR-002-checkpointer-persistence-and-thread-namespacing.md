# ADR-002: Checkpointer Persistence and Thread Namespacing

## Status
Accepted

## Context
Mock interview coaching and feedback reflection are multi-turn, stateful interactions. Sessions must pause and resume across network drops and server restarts without loss of state. Simultaneously, feedback submissions must not overwrite or corrupt interview coaching histories sharing identical identifier spaces.

## Decision
1. In production, use `AsyncPostgresSaver` backed by PostgreSQL connection pooling for resilient checkpoint persistence.
2. In unit test suites, use hermetic `MemorySaver` instances with unique session IDs to guarantee test isolation.
3. Enforce strict thread namespacing:
   - Interview sessions use client/server generated interview thread IDs (`thread_...`).
   - Reflector submissions automatically prefix or isolate their thread scope (`feedback:{thread_id}`) to prevent cross-graph state corruption.
4. Validate thread ownership on WebSocket connect using JWT authentication, preventing cross-tenant thread hijacking.

## Consequences
- **Positive:** Interviews survive pod restarts and network reconnects. Thread isolation prevents state corruption between concurrent agents.
- **Negative:** Requires running checkpoint table bootstrap migrations (`checkpointer.setup()`) during application lifespan initialization.
