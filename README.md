# Career-OS

Stateful AI multi-agent operating system designed to automate and optimize the end-to-end tech career lifecycle: job discovery, company intelligence extraction, evidence-grounded CV tailoring with cyclic ATS optimization, and resumable technical interview coaching.

---

## Architecture Overview

Career-OS follows a decoupled architecture: the React frontend serves strictly as a presentation layer, while all multi-agent orchestration, LLM inference, and state persistence reside within the FastAPI backend using LangGraph.

```mermaid
flowchart TD
    subgraph Frontend["Presentation Layer (React + Vite)"]
        UI["SPA Interface<br/>(TailwindCSS)"]
        WSClient["WebSocket Client<br/>(Streaming & Resumption)"]
    end

    subgraph API["FastAPI Transport Boundary"]
        CORS["Strict CORS & Security Headers"]
        Auth["JWT & WebSocket Auth Guard"]
        Router["REST Routers & WS Endpoints"]
        Metrics["Prometheus /metrics"]
    end

    subgraph Agents["LangGraph Multi-Agent Workflows"]
        Hunter["Hunter Agent<br/>(Job Board Discovery)"]
        Intel["Intel Agent<br/>(Exa Scraper & Tech Stack)"]
        Profiler["Profiler Agent<br/>(Tone & Constraints)"]
        Tailor["Tailor Agent<br/>(Semantic Evidence Synthesis)"]
        ATS["ATS Agent<br/>(Loop Guard <= 3 Revisions)"]
        Coach["Coach Agent<br/>(Interactive Technical Mock)"]
        Reflector["Reflector Agent<br/>(Prompt Weight Tuning)"]
    end

    subgraph Persistence["Storage & Memory Tiers"]
        PGSaver["PostgresSaver<br/>(Short-Term Checkpoints)"]
        PGVector["PostgreSQL + pgvector<br/>(1536-dim HNSW Vector Store)"]
        Relational["SQLAlchemy ORM<br/>(user_profile, job_listing, dossier)"]
    end

    UI -->|REST API| CORS --> Auth --> Router
    WSClient <-->|WebSocket Frames| Auth
    Router --> Agents
    Hunter & Intel & Profiler --> Tailor --> ATS
    ATS -.->|Score < 75% & Rev < 3| Tailor
    Coach <--> Reflector
    Agents <--> PGSaver
    Agents <--> PGVector
    Agents <--> Relational
    API --> Metrics
```

---

## Persistence Tiers

| Tier | Technology | Purpose |
|------|------------|---------|
| **Short-Term Checkpoints** | `langgraph.checkpoint.postgres.AsyncPostgresSaver` | Pausable, resumable multi-turn WebSocket mock interviews across reconnections and server restarts. |
| **Semantic Vector Store** | PostgreSQL + `pgvector` with HNSW Index | 1536-dimensional cosine similarity matching of candidate career blocks (`cv_block`) against job requirements. |
| **Relational Storage** | PostgreSQL + SQLAlchemy 2.0 Async | Long-term entities: `user_profile`, `job_listing`, `company_dossier`, `cv_block`, `feedback_log`, `job_application`. |

---

## Quickstart

### 1. Prerequisites
- Docker & Docker Compose (or Python 3.12+ and Node.js 20+)
- PostgreSQL 16 with pgvector extension (if running locally without Docker)

### 2. Configuration (`.env`)
The project uses a **centralized `.env` file** at the root of the repository for both backend and frontend configuration.

```bash
# Clone the repository
git clone https://github.com/your-username/career-os.git
cd career-os

# Initialize the centralized environment file
make .env
```

*Note: You only need one `.env` file at the root. The frontend Vite server and backend FastAPI server both read from this root `.env`.*

### 3. Run with Docker Compose
To launch the full stack (database, backend, frontend):

```bash
make docker-up
```

- Frontend: `http://localhost:3000` (or `http://localhost:5173`)
- Backend API: `http://localhost:8000`
- API Docs (Swagger UI): `http://localhost:8000/docs`
- Stop the stack: `make docker-down`

### 4. Local Development Setup
If you prefer running services outside of Docker, use the included Makefile targets:

```bash
# Set up Python venv and NPM dependencies (first time only)
cd backend && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt && cd ..
cd frontend && npm install && cd ..

# Verify environment and display start commands
make dev

# Run backend development server (reads from root .env)
make run-backend

# Run frontend development server (reads from root .env)
make run-frontend
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Deployment environment (`development`, `test`, `production`). |
| `APP_DEBUG` | `false` | Enables SQLAlchemy SQL statement echoing (disabled in prod). |
| `DATABASE_URL` | Derived | Connection string (`postgresql+psycopg://user:pass@host:5432/db`). |
| `SECRET_KEY` | Dev default | Cryptographic secret for signing JWT access tokens (>= 32 chars). |
| `GEMINI_API_KEY` | `None` | Google Gemini API key. If unset, uses hermetic `MockChatModel`. |
| `JSEARCH_API_KEY`| `None` | RapidAPI JSearch key for live job board scraping (falls back to fixtures). |
| `EXA_API_KEY`    | `None` | Exa API key for neural company intelligence web scraping. |
| `APOLLO_API_KEY` | `None` | Apollo API key for firmographics and recruiter contact search. |
| `CORS_ORIGINS`   | `["http://localhost:5173", "http://localhost:3000"]` | Whitelisted frontend origins. |
| `ATS_PASS_THRESHOLD` | `75.0` | Minimum score percentage required to pass ATS evaluation. |
| `MAX_REVISIONS`  | `3` | Maximum cyclic revisions between Tailor and ATS agents. |
| `VITE_API_URL`   | `http://localhost:8000` | REST API URL for the frontend. |
| `VITE_WS_URL`    | `ws://localhost:8000` | WebSocket API URL for the frontend. |

---

## API & WebSocket Endpoints

### REST Endpoints
- `POST /api/jobs/search`: Discover target roles filtered by query, location, and visa sponsorship.
- `GET /api/applications/`: Track applied jobs, interview stages, and outcomes.
- `POST /api/cv/generate`: Synthesize tailored CV draft and evaluate cyclic ATS compatibility.
- `POST /api/cv/embed`: Ingest raw resume text and index 1536-dim semantic embeddings.
- `POST /api/feedback`: Submit candidate critique to the Reflector agent to calibrate interview tone and depth.
- `GET /metrics`: Prometheus text-format application and database connection pool metrics.
- `GET /health`: Health probe returning service, environment, and live database status.

### WebSocket Interview Protocol
- Endpoint: `ws://localhost:8000/api/interview/{thread_id}?job_id=...&token=...`
- Bi-directional frames:
  - Client Send: `{"type": "message", "content": "..."}` or `{"type": "ping"}`
  - Coach Receive: `{"type": "message", "sender": "coach", "content": "...", "turn": 1}`
  - Keepalive: `{"type": "pong"}`
  - Error: `{"type": "error", "title": "...", "message": "..."}`

---

## Utilities

### Database Backups
A utility script `scripts/backup_db.sh` is provided to securely dump the PostgreSQL database, including `pgvector` schemas. It automatically sources the root `.env` to authenticate.

```bash
./scripts/backup_db.sh
```

---

## Testing & Quality Gates

Run the verification suite locally before committing:

```bash
# Code formatting
make format

# Static linting & Type analysis (ruff + mypy)
make lint

# Hermetic test suite (zero external network dependencies)
make test

# Frontend build check
make build
```

---

## Architecture Decision Records (ADRs)

Detailed architectural rationale and design choices are documented in `doc/adr/`:
- [ADR-001: pgvector Schema and 1536-Dimensional Semantic Embeddings](doc/adr/ADR-001-pgvector-schema-and-embedding-dimensions.md)
- [ADR-002: Checkpointer Persistence and Thread Namespacing](doc/adr/ADR-002-checkpointer-persistence-and-thread-namespacing.md)
- [ADR-003: Agent Graph Decomposition and ATS Loop Guard](doc/adr/ADR-003-agent-graph-decomposition-and-ats-loop-guard.md)
- [ADR-004: Foreign Key Strict RESTRICT Deletion Policy](doc/adr/ADR-004-foreign-key-strict-restrict-deletion-policy.md)
- [ADR-005: LLM Provider Abstraction and Google Gemini Integration](doc/adr/ADR-005-llm-provider-abstraction-and-gemini-integration.md)

---

## License
MIT
