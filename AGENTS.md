# AGENTS.md — Career-OS Development Guidelines

All agents operating in this workspace must strictly follow the rules, architecture standards, and development workflows defined in:
- [PROJECT_RULES.md](file:///home/bkar/dev/projects/career-os/PROJECT_RULES.md)
- [MASTER_SPEC.md](file:///home/bkar/dev/projects/career-os/MASTER_SPEC.md)

### Key Directives at a Glance:
1. **Decoupled Architecture:** React frontend is strictly a presentation layer. All agent orchestration, state management, and LLM calls happen in FastAPI via LangGraph.
2. **Persistence Tiers:**
   - Short-term: LangGraph with `PostgresSaver` for thread execution checkpointing (interview pause/resume).
   - Long-term: PostgreSQL via SQLAlchemy (`user_profile`, `job_listing`, `company_dossier`).
   - Semantic: PostgreSQL with `pgvector` for career blocks (`cv_block`).
3. **Python & FastAPI Standards:**
   - Strict typing (`ruff`, `mypy`), `async`/`await` for I/O.
   - Module-level imports (PEP 8) — no inline imports.
   - Singular table names (`user_profile`, `cv_block`).
   - `ON DELETE RESTRICT` default for foreign keys.
4. **Agent Workflow & Loop Guards:**
   - ATS evaluation loop (<75% routes back to tailor) must enforce bounded retry limits.
   - Resumable WebSocket mock interviews keyed on `thread_id`.
5. **Testing & Tooling:**
   - AAA pattern, hermetic test isolation with mocked external APIs (JSearch, Exa, Apollo).
   - `ruff format . && ruff check --select I --fix .` before handoff.
   - Conventional Commits via `commit-message` skill.

