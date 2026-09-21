# Master Project Specification: Stateful Career Operating System

## 1. System Objectives & Architecture Overview
This project builds a stateful, multi-agent AI career operating system. The system dynamically routes between multiple CV versions, conducts deep research on target companies, simulates ATS (Applicant Tracking System) evaluations, and provides interactive, resumable interview coaching.

**Architectural Strictures:**
*   **Complete Decoupling (API-First):** The React frontend is strictly a presentation layer. All agentic workflows, LLM calls, and state management occur within the FastAPI backend. 
*   **State Management & Persistence:** 
    *   **Short-term (Execution State):** LangGraph with `PostgresSaver` handles thread-level checkpointing so the Interview Coach can pause/resume asynchronously.
    *   **Long-term (Relational):** PostgreSQL via SQLAlchemy stores User Profiles (including H-1B/OPT constraints), Job Listings, Company Dossiers, and user feedback.
    *   **Semantic Storage (Vector):** PostgreSQL with the `pgvector` extension stores chunked JSON blocks of the user's career achievements for targeted retrieval.

## 2. Workspace Directory Structure
The subagents must construct this exact monolithic repository structure:

```text
/career-os-workspace
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application, REST & WebSocket routers
│   │   ├── core/                   # Database connection (SQLAlchemy + psycopg pool)
│   │   ├── models/                 # SQLAlchemy schemas (Profile, Job, CVBlock)
│   │   ├── agents/
│   │   │   ├── graph.py            # LangGraph StateGraph & PostgresSaver setup
│   │   │   ├── state.py            # TypedDict definitions for graph state
│   │   │   ├── nodes/              # Profiler, Hunter, Intel, Tailor, ATS, Coach, Reflector
│   │   │   └── tools/              # Tool integrations (JSearch, Exa, Apollo)
│   ├── requirements.txt
│   └── alembic/                    # Database migrations
├── frontend/
│   ├── src/
│   │   ├── components/             # React UI (ATS Scorecard, CV Preview, Chat Window)
│   │   ├── services/               # Axios REST clients & WebSocket managers
│   │   ├── pages/                  # Dashboard, InterviewSimulator
│   │   └── App.jsx                 # Main application routing
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml              # PostgreSQL + pgvector instance
```

## 3. Execution Phases for Antigravity Agents

### Phase 1: Infrastructure & Backend Initialization
**Instructions for Subagent:**
1. **Docker Environment:** Generate `docker-compose.yml` to spin up a PostgreSQL instance configured with the pgvector extension (e.g., `ankane/pgvector` image) exposed on port 5432.
2. **Dependencies:** Create `backend/requirements.txt` with: `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg[binary]`, `pgvector`, `langgraph`, `langgraph-checkpoint-postgres`, `langchain`, `pydantic`.
3. **FastAPI Scaffold:** Scaffold `backend/app/main.py` with FastAPI and basic CORS middleware allowing localhost frontend connections.
4. **Relational Models:** Create the SQLAlchemy models in `backend/app/models/`:
   - `UserProfile` (visa constraints, remote preferences, tone directives)
   - `JobListing` (URL, raw description, ATS requirements)
   - `CompanyDossier` (tech stack, recent news, business model)
   - `CVBlock` (including a Vector column for embeddings)

### Phase 2: LangGraph Orchestrator & State Management
**Instructions for Subagent:**
1. **State Definition:** In `backend/app/agents/state.py`, define a TypedDict for the graph state containing: `current_job_id`, `company_dossier`, `cv_draft`, `ats_score`, `interview_history`, and `feedback_logs`.
2. **Node Scaffolding:** Create placeholder Python functions in `backend/app/agents/nodes/` for the core agents:
   - `profiler_node`: Evaluates baseline constraints and updates DB context.
   - `hunter_node`: Executes job board API calls.
   - `intel_node`: Executes multi-step web scraping for target company tech stacks.
   - `tailor_node`: Queries pgvector for CV blocks and assembles the draft.
   - `ats_node`: Scores the draft and routes back to tailor_node if the score is <75%.
   - `coach_node`: Manages the stateful mock interview simulation.
   - `reflector_node`: Synthesizes user feedback into permanent prompt weights in PostgreSQL.
3. **Graph Compilation:** In `backend/app/agents/graph.py`, implement the LangGraph StateGraph. Configure `PostgresSaver.from_conn_string()` to persist thread execution state automatically to the PostgreSQL database.

### Phase 3: API Gateway & WebSocket Implementation
**Instructions for Subagent:**
1. **REST Endpoints:** Build the following routes in `backend/app/main.py`:
   - `POST /api/jobs/search` (Receives constraints, triggers Hunter & Intel sequence)
   - `POST /api/cv/generate` (Receives job_id, triggers Tailor & ATS evaluation loop)
   - `POST /api/feedback` (Receives user review text, triggers Reflector logic)
2. **WebSocket Endpoint:** Build `ws://localhost:8000/api/interview/{thread_id}`. This endpoint must stream messages bi-directionally to the LangGraph coach_node, using the `thread_id` to retrieve the exact conversational checkpoint from `PostgresSaver`.

### Phase 4: React Frontend (Presentation Layer)
**Instructions for Subagent:**
1. **Initialization:** Scaffold a Vite + React project in `/frontend`. Configure TailwindCSS and install `lucide-react`.
2. **Component Architecture:**
   - Build a `Dashboard` page to fetch matched jobs from the REST API and display Company Dossiers.
   - Build an `ATSCard` component to visually display the cyclic pass/fail score of the generated CV.
   - Build the `InterviewSimulator` component that connects to the FastAPI WebSocket endpoint, maintaining the chat interface and rendering the Strategist's technical prep sheet.
3. **State Logic:** Implement React Hooks to manage the active `thread_id` so users can pause an interview, navigate away, and resume seamlessly using the backend `PostgresSaver` memory.

