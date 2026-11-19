---
name: sdlc-tier-selection
description: Use to choose the Low, Medium or High tier variant for each implementation and QA task, based on size, risk and history - and to send complex tasks back to the Planner to be split. Orchestrator only.
---

# Tier selection

The Orchestrator, not the worker, decides how much reasoning a task needs. A lower-tier agent never
judges its own required tier. Score each task, pick a tier, and record a one-line reason in the ledger.

## Score
| Factor | Points |
|---|---|
| Files touched: 1-2 / 3-5 / 6+ | 0 / 1 / 2 |
| Changes existing code (not just new files) | +1 |
| Changes a public interface, shared library or contract | +2 |
| Risk area: authentication, authorisation, payments or money calculations, PII, concurrency, data migration on existing data | +3 |
| No existing tests around the changed code | +1 |
| Planner marked the task `complexity: high` | +3 |
| Task already failed QA once (rework) | +2 |

## Tier
| Score | Tier | Action |
|---|---|---|
| 0-2 | Low | Dispatch `<Role>-<Lane>-Low` |
| 3-5 | Medium | Dispatch `<Role>-<Lane>-Medium` |
| 6-8 | High | Dispatch `<Role>-<Lane>-High` |
| 9+ | **Complex** | Do not dispatch. Send to the Planner (`mode: revise`, scope: this task) to split it into smaller tasks, then score the new tasks |

Also treat a task as complex if it fails at High tier, or touches more than `limits.max_files_per_task` files.
If the Planner says a complex task cannot be split, dispatch it at High and flag it for the user at Gate 2.

## Floors
- Postgres: Low only for purely additive changes that do not touch existing rows (new table, nullable column, index on a new table). Changes to existing tables: Medium at least. Data migration or backfill on existing rows: High.
- Integration check (`contract-check`): always High.
- QA is never more than one tier below its implementer task's tier.
- A rework attempt is never lower than the tier of the failed attempt.

## Agents and models
| Tier | Implementer | QA review depth |
|---|---|---|
| Low | `Impl-<Lane>-Low` (low-cost model) | Plan conformance, acceptance criteria, tests pass, lint and format clean |
| Medium | `Impl-<Lane>-Medium` (low-cost model) | Low, plus correctness and edge cases, error handling, coding standards, test quality |
| High | `Impl-<Lane>-High` (strong model) | Medium, plus design fit, security, performance, reuse, contract adherence |

Each tier variant's model is set in its agent file. `config.yaml` under `models` documents the mapping;
change both together. If a mid-priced model becomes available, use it for the Medium variants.

Record: `T4 tier=high (score 7: payments +3, shared lib +2, 3 files +1, existing code +1)`.
