# Career-OS Project Rules & Development Standards

## 1. Project Specifications & Architectural Context

- **Source of Truth:** All development must strictly align with the [Master Project Specification](file:///home/bkar/dev/projects/career-os/MASTER_SPEC.md).
- **Architecture Decisions:** Architectural shifts or major design choices must be captured in Architecture Decision Records (ADRs) under `doc/adr/` (e.g., `ADR-001-pgvector-schema.md`).
- **Naming Conventions:** Never refer to agent configuration or internal scratch files by raw filenames in user-facing documentation. Refer to specifications by topic or title (e.g., "Master Project Specification §2", "ADR-001").

---

## 2. Development Quickstart (Local Stack Bootstrap)

Run these steps in order when bootstrapping or validating the local environment:

### Step 1: Start PostgreSQL with pgvector
```bash
# From project root — spins up PostgreSQL with pgvector extension on port 5432
docker compose up -d
```

### Step 2: Backend Environment & Formatting
```bash
cd backend
# Ruff formatting and sorted import optimization (PEP 8)
../.bin/uv run ruff format . && ../.bin/uv run ruff check --select I --fix .
# Run backend pytest suite against local test database
../.bin/uv run pytest
```

### Step 3: Frontend Validation
```bash
cd frontend
npm run lint
npm test
```

### Step 4: Start Development Servers
```bash
# Backend (FastAPI on port 8000)
cd backend && ../.bin/uv run uvicorn app.main:app --reload --port 8000

# Frontend (Vite on port 5173)
cd frontend && npm run dev
```

---

## 3. First-Time-Right Implementation Workflow

### Phase 1: Clarify, Spec & Explore
- **Understand First:** Never write code immediately. Clarify all acceptance criteria and edge cases.
- **Explore Baseline:** Inspect existing database models, agent state definitions, and reusable UI components before creating new ones.
- **Architecture Alignment:** Ensure strict decoupling. The React frontend is purely a presentation layer; all business logic, LLM calls, and state management belong in the FastAPI backend.

### Phase 2: Architecture & Planning
- **Interfaces First:** Define public API contracts, Pydantic schemas, and LangGraph `StateGraph` TypedDict definitions before implementing internal logic.
- **Persistence Strategy:**
  - **Short-term:** LangGraph `PostgresSaver` for thread-level execution checkpoints (e.g., resumable mock interviews).
  - **Long-term:** PostgreSQL via SQLAlchemy for relational domain models (`UserProfile`, `JobListing`, `CompanyDossier`, feedback).
  - **Semantic:** PostgreSQL with `pgvector` for embedding storage and similarity search (`CVBlock`).

### Phase 3: Atomic TDD Implementation
- **Red → Green → Refactor:** Write tests first for agent routing, API endpoints, and vector search. Minimum passing code, aggressive refactoring.
- **Atomic Steps:** Keep changes focused; ensure test suites pass after each change.
- **Scope Discipline:** Strictly avoid scope creep.

### Phase 4: Continuous Self-Review

#### A. Backend & FastAPI Standards
- **Strict Typing:** Enforce type annotations on all functions and routes; validate with `ruff` and `mypy`.
- **Async/Await:** Use `async`/`await` for all database, vector retrieval, and network I/O.
- **Configuration:** Manage settings strictly via Pydantic `BaseSettings` reading from `.env`.
- **Database Table Naming:** Use lowercase singular names (`user_profile`, `job_listing`, `company_dossier`, `cv_block`).
- **Foreign Keys:** Default to blocking cascade deletion (`ON DELETE RESTRICT` or omit `ON DELETE`) unless explicitly designated otherwise.
- **Layered Decoupling:**
  - `backend/app/models/`: Pure SQLAlchemy ORM and pgvector schema declarations. No business logic.
  - `backend/app/core/`: Database engine, connection pooling, and configuration.
  - `backend/app/agents/`: State definitions (`state.py`), workflow compilation (`graph.py`), agent nodes (`nodes/`), and external tool wrappers (`tools/`).
  - `backend/app/api/` or `main.py`: Thin REST and WebSocket transport layers delegating directly to agent graph or service layers.
- **Module-Level Imports (PEP 8):** All imports must reside strictly at the module top level. Never write inline or local `import` statements inside functions, classes, or test functions.

#### B. LangGraph & Agent Orchestration Standards
- **State Immutability:** State changes in nodes must return partial state update dictionaries adhering to `backend/app/agents/state.py`.
- **Loop Guards:** Cyclic graphs (e.g., `ats_node` routing back to `tailor_node` on score `< 75%`) must enforce a maximum retry counter (e.g., `max_revisions = 3`) to prevent infinite evaluation loops.
- **Stateful Checkpointing:** Thread sessions in WebSockets must pass a unique `thread_id` to `PostgresSaver` to guarantee seamless pause and resume capability.

#### C. React & Frontend Standards
- **Responsive Layouts:** Every screen must adapt across mobile, tablet, and desktop viewports with Tailwind CSS.
- **Layout Constraints:** Avoid unbounded wide widgets on wide monitors (use `max-w-4xl`, `max-w-6xl`, or responsive grid containers).
- **Three UI Lifecycle States:** Every data-driven or async component must explicitly handle:
  1. **Loading State:** Skeletons or spinners with interactive controls disabled.
  2. **Error State:** Clear, actionable error messages with a retry action.
  3. **Data / Empty State:** Accurate rendering of content or helpful empty-state guidance.
- **Thread Session Persistence:** Manage `thread_id` cleanly in React state/hooks to allow users to navigate away and return to ongoing mock interviews.

#### D. Security & Privacy
- **Boundary Validation:** Validate all inputs using Pydantic schemas on the backend and validation helpers on the frontend.
- **No Hardcoded Secrets:** Never commit API keys (OpenAI, Gemini, Exa, JSearch, Apollo) or database credentials.
- **Safe Logging:** Never emit raw user PII (names, contact info, resume text) in application logs. Use sanitized IDs (`user_id`, `job_id`, `thread_id`, `correlation_id`).
- **OWASP Compliance:** Prevent SQL injection (use parameterized SQLAlchemy queries), avoid unsafe deserialization, and enforce CORS restrictions.

#### E. Error Handling & Observability
- Propagate `X-Correlation-ID` across HTTP headers and WebSocket messages.
- Return structured error details (RFC 7807 Problem Details or structured Pydantic error models).
- Use structured logging (`logging` or `structlog`). No bare `print()` statements in production code.

### Phase 5: Verification & Handoff
- **Formatting & Linting:**
  - Python: `ruff format . && ruff check --select I --fix .`
  - JavaScript/React: `npx prettier --write . && npm run lint`
  - Ensure line lengths strictly conform to style standards (88 chars for Python).
- **Atomic Commits:** Use Conventional Commits with scope tags (e.g., `feat(agents):`, `fix(ats):`, `test(vector):`). Subject line ≤ 72 chars.
- **Skill Usage:** Use the `commit-message` skill to generate structured commit messages based on `git diff`.

---

## 4. Testing Architecture & Isolation Standards

- **AAA Pattern:** Arrange, Act, Assert clearly demarcated in each test.
- **Hermetic Test Isolation:** Unit and integration tests must run against a local test database without touching development or production data.
- **Mock External Services:** All external tool calls (JSearch job board, Exa web scraper, Apollo company search, LLM inference) must be strictly mockable in unit and CI test runs.
- **WebSocket Streaming Tests:** Include test harnesses validating bidirectional streaming and checkpoint resumption over `/api/interview/{thread_id}`.

