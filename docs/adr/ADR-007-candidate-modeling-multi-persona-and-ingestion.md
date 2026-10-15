# ADR-007: Candidate Modeling, Multi-Modal Ingestion & Multi-Persona Architecture

**Date**: 2026-10-15  
**Status**: Accepted  
**Deciders**: System Architect, Lead Backend Engineer  

---

## Context

Modern job search is structurally dysfunctional for candidates due to three core systemic barriers identified across industry analyses and candidate communities (`r/cscareerquestions`, `r/jobs`, `r/recruitinghell`):

1. **The "Invisible Candidate" Black Box in ATS Platforms:**
   Traditional Applicant Tracking Systems (Workday, Greenhouse, Taleo) do not auto-reject candidates via sentient AI; rather, they serve as internal keyword search engines for recruiters. Candidates whose resumes fail exact string matches or parse poorly sit at the bottom of 500+ applicant databases and are never viewed.
2. **Brittle Document Parsing Penalties:**
   Independent studies and recruiter benchmarks report that over 80% of resumes encounter parsing errors due to multi-column layouts, tables, text boxes, and special symbols. Furthermore, career pivoters and students often lack a polished CV entirely.
3. **The Multi-Persona & Hybrid Competency Reality:**
   Modern engineers do not fit into single monolithic career silos. A developer frequently targets both *Distributed Systems / Python Backend* and *AI/ML Platform* roles. Furthermore, there is significant overlap and high market value in "hybrid" candidates (e.g. Python backend developers equipped with LLM/AI orchestration). Monolithic, single-document resumes force candidates to either compromise their breadth or manually juggle dozens of brittle PDF files.
4. **Third-Party Platform Access Restrictions:**
   LinkedIn’s public API restricts work history and education to enterprise ATS partners under the LinkedIn Talent Solutions Partner program (Recruiter System Connect). Standard OAuth (`openid`, `profile`) returns only basic identity fields. Handshake also restricts student profile access to institutional partners.

---

## Decision

We will decouple user identity from career personas and implement a multi-modal, block-based candidate architecture:

1. **Decoupled User Account and Multi-Persona Model:**
   - **`user_account`**: Owns primary identity, authentication, work authorization (`visa_status`), citizenship, contact details, and master career history.
   - **`candidate_persona`**: Represents targeted career tracks. Every user automatically receives a **Universal / Common Persona** (`is_common_persona = TRUE`) that synthesizes their full breadth (capturing hybrid strengths like Python + AI). Users can create specialized personas (e.g. *AI Infrastructure Engineer*, *Java Enterprise Architect*) with dedicated target roles, prioritized skills, and filtered feeds.
2. **Atomic Semantic Blocks (`cv_block`):**
   - Deconstruct candidate career history into granular, verified accomplishment units structured in the **STAR** method (Situation, Task, Action, Result) with quantified metrics, verified skill tags, and 1536-dimensional vector embeddings (`pgvector`).
   - Support rich achievement categories including **Experience**, **Projects**, **Education**, **Hackathons & Competitions**, and **Open Source Maintainership**.
3. **Multi-Modal Onboarding Pipeline:**
   - **Document Parser**: PDF/DOCX parsing using `pdfplumber` positional layout extraction to prevent column scrambling, fed to the LLM Profiler node for STAR block generation.
   - **LinkedIn Bridge**: Deterministic parser calibrated to LinkedIn's standardized "Save to PDF" format, plus rich text profile paste.
   - **Guided UI Wizard**: 5-step interactive onboarding flow for candidates with no existing resume (students, career pivoters), collecting verified skills, hackathons, and quantified project outcomes.
   - **Staging Review Screen**: Mandatory interactive verification step before persistence, allowing users to correct dates, titles, and metrics.

---

## Consequences

**Positive:**
- **Zero Parsing Loss:** Users review and correct parsed blocks on an interactive staging canvas before storage.
- **Maximum Market Reach for Hybrids:** The Common Persona enables discovery of cross-discipline roles (e.g. AI Backend), while specialized personas allow targeted optimization for specialist openings.
- **High Ingestion Inclusivity:** Students, hackathon winners, and candidates without formal resumes have first-class onboarding parity with seasoned engineers.
- **Composable Semantic Search:** Individual accomplishment blocks can be dynamically matched against specific job requirements with `pgvector`.

**Negative / Trade-offs:**
- Requires managing relationships between user accounts, multiple personas, and master CV blocks via junction tables (`persona_cv_block_rel`).
- Parsing and LLM structuring introduces an initial 5–10 second onboarding latency on resume upload (mitigated with an instant preview and optimistic UI).

**Neutral (Must Be Maintained):**
- Schema evolution remains strictly in `db/migrations/0001_initial_schema.sql` per project rules.
- Foreign keys maintain `ON DELETE RESTRICT` semantics to prevent accidental data loss.

---

## Alternatives Considered

### Option A: Flat Resume Storage with Keyword Tag Array
- **Description:** Store raw PDF text and an array of extracted string keywords.
- **Why Rejected:** Fails to capture context, scale, and quantified impact (e.g., cannot distinguish between college-level Python and 6 years of high-throughput Kafka/Python production experience). Lacks support for multi-persona targeting.

### Option B: Monolithic User Profile Table (1:1 with Account)
- **Description:** Store all role targets and preferences in JSON columns inside a single `user_profile` table.
- **Why Rejected:** Causes severe impedance mismatch when a user wants distinct job matching feeds, tailored resumes, and customized ATS scores for radically different career paths.

---

## References

1. LinkedIn Talent Solutions Developer Portal: [Partner Ecosystem & Scopes](https://learn.microsoft.com/en-us/linkedin/talent/)
2. Reddit discussions on ATS parsing breakdowns and candidate invisibility: [r/cscareerquestions ATS Myth Analysis](https://www.reddit.com/r/cscareerquestions/)
3. Teal & Simplify competitor scans on resume branching and auto-fill fatigue.
4. Career-OS Master Specification: `MASTER_SPEC.md` and `PROJECT_RULES.md`.

