# ADR-003: Agent Graph Decomposition and ATS Loop Guard

## Status
Accepted

## Context
The CV tailoring process involves multiple specialized agents: Profiler (candidate constraints), Hunter (job acquisition), Intel (company research), Tailor (synthesis), and ATS (scoring). Without structural boundaries, cyclical loops could run indefinitely, exhausting LLM tokens and API budgets.

## Decision
1. Retain caller-supplied job definitions (`job_details` or `current_job_id`) in `hunter_node` rather than overwriting with default searches.
2. Ground `tailor_node` synthesis strictly in candidate evidence retrieved from `cv_block` records, preventing hallucination of unproven skills.
3. ATS scoring implements a cyclic feedback loop:
   - When score < `settings.ATS_PASS_THRESHOLD` (75.0%) and `revision_count` < `settings.MAX_REVISIONS` (3), route back to `tailor` with structured feedback on missing keywords.
   - When score >= 75.0% or `revision_count` >= 3, terminate execution (`__end__`).
4. Bound overall graph execution using `recursion_limit=settings.GRAPH_RECURSION_LIMIT` to safeguard against infinite recursion.

## Consequences
- **Positive:** Guarantees deterministic termination, bounds LLM expenditure, and ensures CV contents truthfully reflect candidate records.
- **Negative:** Hard revision ceiling may yield non-passing scores for fundamentally unqualified roles, which is accurately reported to the user.
