---
name: sdlc-task-slicing
description: Use after plan approval to split the approved plan into small, independent implementation tasks with lanes, dependencies and execution waves. Orchestrator only.
---

# Task slicing and dependency scheduling

## Input
The approved `plan.md` for the run: services and files affected, contracts, acceptance criteria and test notes.

## Rules for a good task
1. **One lane, one agent.** Each task belongs to exactly one lane: `python`, `postgres` or `react`.
2. **Small and bounded.** 1-5 files is ideal, 8 at most. Split anything bigger by service, endpoint or component.
3. **Self-contained.** The task envelope must be enough to do it. If a worker would need the whole plan, the task is too vague: split or sharpen it.
4. **Contract first.** Every cross-lane interaction (endpoint, payload, table, event) must be a contract snippet from the plan, attached to both the producing task and the consuming task.
5. **Testable.** Each task has numbered acceptance criteria, and at least one is verified by a test the implementer writes or updates.
6. **No tiny tasks.** Merge tasks under about 20 lines of change in the same lane and service. Each delegation costs a full agent start.
7. **One task per service per wave** for Python, unless the plan explicitly separates modules. Several Python implementers may run in parallel on different services.

## Waves (dependency order)
| Wave | Contains | Why |
|---|---|---|
| W0 | Shared libraries and common modules that other tasks import | Everything else depends on them |
| W1 | Postgres: schema changes and migrations (expand step first) | Backend code needs the schema |
| W2 | Python services and React UI, **in parallel** | Both work against the agreed contract. React may use a mock of the endpoint if the backend is not yet DONE |
| W3 | Integration check (only if more than one lane changed) | Confirms the lanes fit together |

Empty waves are skipped. A task moves to the earliest wave in which all its dependencies are DONE.

## Output - write this table to the ledger
```
| id | wave | lane | agent | service/component | goal (one line) | files | depends_on | tier | status | attempts |
|----|------|------|-------|-------------------|-----------------|-------|------------|------|--------|----------|
| T1 | W1 | postgres | Impl-Postgres | orders-db | add orders.status column + migration | migrations/0042_*.py | - | medium | TODO | 0 |
| T2 | W2 | python | Impl-Python | orders-api | PATCH /orders/{id}/status | app/api/orders.py, app/models/order.py, tests/api/test_orders.py | T1 | medium | TODO | 0 |
| T3 | W2 | react | Impl-React | order-page | status dropdown calls PATCH endpoint | src/pages/Order.tsx, src/api/orders.ts | contract C1 | low | TODO | 0 |
```
The `agent` column holds the lane family. At dispatch the tier is appended: `Impl-Postgres` + `medium` -> `Impl-Postgres-Medium`.
Then keep, per task, the contract IDs and acceptance criteria numbers it covers, so the envelope can be built without re-reading the plan.

**All three lanes in one wave:** if the plan has no schema change, there is no W1, and Python and React run together in W2. If there is a schema change, Postgres runs first (W1), because Python tests need the migrated schema.

## Checklist before dispatching
- [ ] Every acceptance criterion in the plan is covered by at least one task.
- [ ] Every contract has a producer task and, if used, a consumer task.
- [ ] No two tasks in the same wave change the same file.
- [ ] Dependencies point only to earlier waves.
