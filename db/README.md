# Database Architecture & Pure SQL Migrations Guide

Career-OS utilizes PostgreSQL with `pgvector` for long-term relational persistence and dense semantic resume matching.
All database schemas are authored directly in pure PostgreSQL DDL under `db/migrations/`, eliminating the abstraction overhead and complexity of Alembic.

---

## 1. Directory Structure

```text
db/
├── migrate.py                     # Self-contained migration CLI runner & tracker
├── README.md                      # Architecture documentation and operation guide
└── migrations/
    └── 0001_initial_schema.sql     # Single canonical sequential baseline schema DDL
```

---

## 2. Why Pure SQL Instead of Alembic?

1. **Readability & Direct Authority:** Raw SQL DDL allows engineers and DBAs to inspect indexes, table constraints, triggers, and foreign keys directly without navigating complex Python auto-generated operation graphs (`op.create_table`, `op.add_column`).
2. **Explicit Dependency & Execution Order:** Migration files in `db/migrations/` use sequential numeric prefixes (e.g. `0001_initial_schema.sql`), making execution order immediately apparent.
3. **Lightweight & Transparent Tracking:** Instead of Alembic's complex revision DAG, a transparent `schema_migrations` table records file versions, execution times, and SHA-256 checksums.

---

## 3. Required PostgreSQL Extensions

### 3.1 `uuid-ossp`
* **Purpose:** Generates RFC 4122 compliant version 4 UUIDs (`uuid_generate_v4()`).
* **Why Career-OS Needs It:**
  1. **Decentralized Primary Keys:** Asynchronous crawler workers, ingestion pipelines, and background daemons can generate collision-free unique IDs before sending database writes.
  2. **Security & Anti-Enumeration:** Sequential integer IDs (e.g., `/jobs/1`, `/jobs/2`) leak platform velocity and enable automated scraping attacks. UUIDv4 keys eliminate enumeration risks.

### 3.2 `vector` (`pgvector`)
* **Purpose:** High-performance vector operations and Approximate Nearest Neighbor (ANN) search.
* **Why Career-OS Needs It:**
  1. **Semantic Resume Synthesis:** Resume tailoring matches candidate accomplishments (`cv_block`) against job requirements using dense 1536-dimensional semantic embeddings.
  2. **Sub-Millisecond Cosine Matching:** Native cosine distance operator (`<=>`) computes similarities as `1 - (embedding <=> target_vector)`.
  3. **HNSW Indexing:** Hierarchical Navigable Small World (HNSW) index structures (`m=16, ef_construction=64`) execute in sub-milliseconds without relying on proprietary third-party vector databases.

---

## 4. Entity-Relationship & Table Overview

Career-OS enforces strict singular table naming and `ON DELETE RESTRICT` foreign keys across all 13 tables:

| Table | Purpose | Key Relationships |
| :--- | :--- | :--- |
| `ats_provider` | Root catalog of ATS engines (Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Custom) | Referenced by `ats_board`, `job_listing`, `ingestion_run` |
| `industry_sector` | Standardized, snake_case industry categories (e.g. `hft_quant_trading`, `fintech`) | Referenced by `ats_board`, `company_dossier`, `job_listing` |
| `user_profile` | Candidate profile, preferences, target roles | Parent of `cv_block`, `application`, `feedback_log` |
| `cv_block` | Candidate experience blocks with 1536-dim vector embeddings | Foreign key to `user_profile` |
| `company_dossier` | Researched company tech stacks, recent news, culture, and provenance | Referenced by `ats_board`, `job_listing` |
| `ats_board` | Tracked career boards with sync schedule and consecutive failure counters | Foreign key to `ats_provider`, `industry_sector`, `company_dossier` |
| `job_listing` | Ingested jobs with location hierarchy, workplace modality, remote scope, and visa policies | Foreign key to `ats_board`, `ats_provider`, `industry_sector`, `company_dossier` |
| `application` | User job applications and stage status | Foreign key to `user_profile`, `job_listing` |
| `feedback_log` | Candidate feedback for prompt weight optimization | Foreign key to `user_profile` |
| `ingestion_run` | Telemetry for board sync runs (new, updated, closed counts, latency) | Foreign key to `ats_board`, `ats_provider` |
| `ingestion_task` | Asynchronous worker queue (`SELECT FOR UPDATE SKIP LOCKED`) | Foreign key to `ats_board`, `ats_provider` |
| `provider_usage` | Rate limit counters and quota tracking per period | Foreign key to `ats_provider` |
| `provider_state` | Circuit breaker tracking and cooldowns per ATS provider | Foreign key to `ats_provider` |

---

## 5. Using the Migration Runner (`db/migrate.py`)

The runner automatically loads the database connection string from `.env` or `DATABASE_URL`.

### 5.1 Common Commands

```bash
# Apply all pending migrations sequentially
python db/migrate.py

# Or using the root Makefile shortcut
make db-migrate

# Check current status of all migrations and disk checksums
python db/migrate.py --status

# Baseline an existing database without re-executing DDL
python db/migrate.py --baseline
```

### 5.2 Tracking Table & Tampering Protection

Migrations are tracked in the `schema_migrations` table:
```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,      -- e.g. "0001_initial_schema.sql"
    checksum VARCHAR(64) NOT NULL,         -- SHA-256 digest
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    execution_time_ms INTEGER NOT NULL
);
```

Before applying pending migrations, `db/migrate.py` re-computes the SHA-256 checksum of every previously applied file on disk. If a file has been modified after being applied, it alerts the operator and stops execution, preventing silent schema drift.

