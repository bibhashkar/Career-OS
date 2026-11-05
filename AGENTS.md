# AGENTS.md — Career-OS Development Guidelines

All agents operating in this workspace must strictly follow the rules, architecture standards, and development workflows defined in:
- [PROJECT_RULES.md](file:///home/bkar/dev/projects/career-os/PROJECT_RULES.md)
- [MASTER_SPEC.md](file:///home/bkar/dev/projects/career-os/MASTER_SPEC.md)

### Key Directives at a Glance:
1. **Quad-Perspective Planning Standard:**
   Every feature, architecture document, refactor, and system design MUST be planned and evaluated across four distinct expert lenses:
   - **🏛️ Expert Software Architect:** System modularity, clean boundaries, decoupled contracts, relational/vector data integrity, resilient design patterns, and horizontal scalability.
   - **⚙️ DevOps & Platform Engineer:** Containerization, environment parity, CI/CD gates, distributed observability (OTel/Prometheus/JSON logs), health probes, resource limits, and hermetic reproducible runtime.
   - **🎯 Seasoned Product Manager:** User problem statement, JTBD (Jobs To Be Done), target personas, acceptance criteria, edge case recovery, phased release roadmap, and measurable KPI/success metrics.
   - **🎨 Master UI/UX Designer:** Cognitive ergonomics, progressive disclosure, design system consistency, responsive viewport constraints, micro-interactions, accessibility (WCAG AA), and the strict 3-state UI contract (loading, error + retry, zero/empty state).
2. **Decoupled Architecture:** React frontend is strictly a presentation layer. All agent orchestration, state management, and LLM calls happen in FastAPI via LangGraph.
3. **Persistence Tiers:**
   - Short-term: LangGraph with `PostgresSaver` for thread execution checkpointing (interview pause/resume).
   - Long-term: PostgreSQL via SQLAlchemy (`user_profile`, `job_listing`, `company_dossier`).
   - Semantic: PostgreSQL with `pgvector` for career blocks (`cv_block`).
4. **Python & FastAPI Standards:**
   - Strict typing (`ruff`, `mypy`), `async`/`await` for I/O.
   - Safe `TypedDict` and `RunnableConfig` access: always use `.get()` with type-narrowing; never subscript non-required keys with `d[k]`.
   - Export and reuse `Literal` type aliases; avoid implicit string widening.
   - Module-level imports (PEP 8) — no inline imports.
   - Singular table names (`user_profile`, `cv_block`).
   - `ON DELETE RESTRICT` default for foreign keys.
5. **Agent Workflow & Loop Guards:**
   - ATS evaluation loop (<75% routes back to tailor) must enforce bounded retry limits.
   - Resumable WebSocket mock interviews keyed on `thread_id`.
6. **Testing & Tooling:**
   - AAA pattern, hermetic test isolation with mocked external APIs (JSearch, Exa, Apollo).
   - `ruff format . && ruff check --select I --fix .` before handoff.
   - Conventional Commits via `commit-message` skill.

