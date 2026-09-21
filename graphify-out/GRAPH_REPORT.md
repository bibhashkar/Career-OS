# Graph Report - career-os  (2026-09-20)

## Corpus Check
- Corpus is ~744 words - fits in a single context window. You may not need a graph.

## Summary
- 24 nodes · 29 edges · 5 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 744 input · 850 output

## Community Hubs (Navigation)
- Agent Orchestration & Checkpointing
- CV Tailoring & ATS Scoring
- Frontend UI & Live Simulation
- System Architecture & API Backend
- Relational Data Models

## God Nodes (most connected - your core abstractions)
1. `LangGraph Orchestrator` - 9 edges
2. `PostgreSQL Relational Storage` - 5 edges
3. `React Frontend` - 4 edges
4. `API-First Decoupled Architecture` - 3 edges
5. `PostgresSaver Checkpointing` - 3 edges
6. `Tailor Node` - 3 edges
7. `Coach Node` - 3 edges
8. `ATS Cyclic Feedback Loop` - 3 edges
9. `FastAPI Backend` - 2 edges
10. `pgvector Semantic Storage` - 2 edges

## Surprising Connections (you probably didn't know these)
- `API-First Decoupled Architecture` --references--> `React Frontend`  [EXTRACTED]
  MASTER_SPEC.md → MASTER_SPEC.md  _Bridges community 3 → community 2_
- `FastAPI Backend` --references--> `LangGraph Orchestrator`  [EXTRACTED]
  MASTER_SPEC.md → MASTER_SPEC.md  _Bridges community 3 → community 0_
- `React Frontend` --references--> `ATSCard Component`  [EXTRACTED]
  MASTER_SPEC.md → MASTER_SPEC.md  _Bridges community 2 → community 1_
- `LangGraph Orchestrator` --references--> `ATS Node`  [EXTRACTED]
  MASTER_SPEC.md → MASTER_SPEC.md  _Bridges community 0 → community 1_
- `PostgresSaver Checkpointing` --references--> `PostgreSQL Relational Storage`  [EXTRACTED]
  MASTER_SPEC.md → MASTER_SPEC.md  _Bridges community 0 → community 4_

## Hyperedges (group relationships)
- **Multi-Agent Workflow** — master_spec_profiler_node, master_spec_hunter_node, master_spec_intel_node, master_spec_tailor_node, master_spec_ats_node, master_spec_coach_node, master_spec_reflector_node [EXTRACTED 1.00]
- **Persistence and State Tiers** — master_spec_postgres_saver, master_spec_postgresql_database, master_spec_pgvector_extension [EXTRACTED 1.00]
- **Frontend Presentation Architecture** — master_spec_dashboard_component, master_spec_ats_card_component, master_spec_interview_simulator_component [EXTRACTED 1.00]

## Communities (5 total, 0 thin omitted)

### Community 0 - "Agent Orchestration & Checkpointing"
Cohesion: 0.33
Nodes (7): Coach Node, Hunter Node, Intel Node, LangGraph Orchestrator, PostgresSaver Checkpointing, Profiler Node, Reflector Node

### Community 1 - "CV Tailoring & ATS Scoring"
Cohesion: 0.33
Nodes (6): ATSCard Component, ATS Cyclic Feedback Loop, ATS Node, CVBlock Model, pgvector Semantic Storage, Tailor Node

### Community 2 - "Frontend UI & Live Simulation"
Cohesion: 0.40
Nodes (5): CompanyDossier Model, Dashboard Component, InterviewSimulator Component, Interview Simulator WebSocket, React Frontend

### Community 3 - "System Architecture & API Backend"
Cohesion: 0.67
Nodes (3): API-First Decoupled Architecture, Stateful Career Operating System, FastAPI Backend

### Community 4 - "Relational Data Models"
Cohesion: 0.67
Nodes (3): JobListing Model, PostgreSQL Relational Storage, UserProfile Model

## Knowledge Gaps
- **7 isolated node(s):** `Stateful Career Operating System`, `UserProfile Model`, `JobListing Model`, `Profiler Node`, `Hunter Node` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 7 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LangGraph Orchestrator` connect `Agent Orchestration & Checkpointing` to `CV Tailoring & ATS Scoring`, `System Architecture & API Backend`?**
  _High betweenness centrality (0.522) - this node is a cross-community bridge._
- **Why does `PostgreSQL Relational Storage` connect `Relational Data Models` to `Agent Orchestration & Checkpointing`, `CV Tailoring & ATS Scoring`, `Frontend UI & Live Simulation`?**
  _High betweenness centrality (0.283) - this node is a cross-community bridge._
- **Why does `PostgresSaver Checkpointing` connect `Agent Orchestration & Checkpointing` to `Relational Data Models`?**
  _High betweenness centrality (0.209) - this node is a cross-community bridge._
- **What connects `Stateful Career Operating System`, `UserProfile Model`, `JobListing Model` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._