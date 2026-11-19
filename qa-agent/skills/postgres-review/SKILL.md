---
name: postgres-review
description: Use when reviewing a completed PostgreSQL/Alembic migration task - tiered checklist for contract match, migration safety, downgrade, locking, backfill and data integrity. Postgres QA agents.
---

# Postgres review checklist

Apply the sections up to your tier. Each tier includes the ones above it.

## Low - plan conformance
- [ ] The migration matches the contract DDL exactly: table and column names, types, nullability, defaults, constraints, indexes.
- [ ] Exactly one migration for the task, with the correct `down_revision`; `alembic heads` shows a single head.
- [ ] `downgrade()` exists and reverses `upgrade()`.
- [ ] The migration was verified (online upgrade -> downgrade -> upgrade, or offline `--sql`), and the result is reported honestly.
- [ ] If the ORM model is in scope, it matches the migration.
- [ ] Naming follows the repo's conventions for constraints and indexes.

## Medium - safety on existing tables
- [ ] No `NOT NULL` column added to an existing table without a server default.
- [ ] No rename or drop of a column or table unless the plan explicitly requires it.
- [ ] Defaults and nullability make sense for rows that already exist.
- [ ] Foreign keys have suitable `ON DELETE` behaviour, as the plan specifies.
- [ ] Indexes support the queries the plan mentions; no duplicate indexes.
- [ ] Re-run online if a database is reachable: `alembic upgrade head`, `alembic downgrade -1`, `alembic upgrade head`.

## High - data and locking risk
- [ ] Backfills are batched and idempotent (safe to run twice).
- [ ] Long-running locks are avoided on large tables (concurrent index creation where the repo supports it; no full-table rewrites without a plan note).
- [ ] Data cannot be lost by `upgrade()`; if `downgrade()` loses data, it is stated in the summary and code comment.
- [ ] Constraints added to existing data will not fail on rows that already violate them (or the plan covers cleaning them first).
- [ ] The expand/contract sequence is respected: the old code still works after `upgrade()`, before the new code is deployed.
- [ ] No hard-coded environment-specific values (schemas, users, tablespaces) unless the repo does this.
