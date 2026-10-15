# ADR-004: Foreign Key Strict RESTRICT Deletion Policy

## Status
Accepted

## Context
Project rules mandate `ON DELETE RESTRICT` as default for relational database foreign keys. An earlier revision of `UserProfile.cv_blocks` declared `cascade="all, delete-orphan"`, creating an architectural contradiction between ORM cascading and database constraints.

## Decision
1. Eliminate `cascade="all, delete-orphan"` on `UserProfile.cv_blocks`.
2. Enforce strict `ON DELETE RESTRICT` at both the PostgreSQL DDL level and SQLAlchemy ORM level across all foreign keys (`user_profile_id`, `job_listing_id`, etc.).
3. Account deletion and data purges (e.g. GDPR Right to Be Forgotten) must be handled explicitly through an audited purge service that deletes child records (`cv_block`, `feedback_log`) in reverse dependency order within a transaction.

## Consequences
- **Positive:** Prevents accidental catastrophic cascading deletes of critical user career history and vector embeddings.
- **Negative:** Deleting a user requires explicit deletion orchestration rather than a single `session.delete(user)`.
