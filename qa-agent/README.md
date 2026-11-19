# QA agents - AI SDLC factory (iteration 1)

Nine QA agents: three lanes (Python, Postgres, React) times three tiers (Low, Medium, High).
Each reviews **one completed task** against its plan slice and returns a clear **PASS or FAIL**, with
findings the Orchestrator can route automatically. The two High-tier Python and React agents also run the
cross-lane **contract check**.

## Design decisions
| Topic | Decision |
|---|---|
| Read-only | QA agents have no edit tool. They find problems and say how to fix them; the implementer fixes them |
| Tiers | Flat, chosen by the Orchestrator. Each tier includes everything below it. QA is never more than one tier below its implementer task |
| Re-running checks | Trust, but verify. Low: area tests. Medium: + lint and type check. High: + format and the full suite |
| Verdict | `FAIL` if there is any `must-fix` finding, otherwise `PASS`. `should-fix` and `nit` are reported at Gate 2 and never block |
| Routing | Each finding has a type: `code`, `test`, `check`, `contract-deviation` go back to the implementer; `plan-gap` goes to the Planner |
| Scope | Only the changed files and their direct impact. QA does not redesign or ask for things the plan did not require |
| Integration | After all lanes are done, `QA-React-High` (or `QA-Python-High`) runs `contract-check`: producer and consumer compared field by field for every contract |
| Models | Low and Medium: Haiku 5.5. High: Sonnet 5.5 |

## Files and where to install them
| File in this folder | Install in the workspace at |
|---|---|
| `agents/qa-python-{low,medium,high}.agent.md` | `.github/agents/` |
| `agents/qa-postgres-{low,medium,high}.agent.md` | `.github/agents/` |
| `agents/qa-react-{low,medium,high}.agent.md` | `.github/agents/` |
| `instructions/qa-protocol.instructions.md` | `.github/instructions/` |
| `skills/python-review/SKILL.md` | `.github/skills/python-review/` |
| `skills/postgres-review/SKILL.md` | `.github/skills/postgres-review/` |
| `skills/react-review/SKILL.md` | `.github/skills/react-review/` |
| `skills/contract-check/SKILL.md` | `.github/skills/contract-check/` |

The QA protocol has no `applyTo`, so it is not loaded into every chat. Each QA agent links to it.

## What each tier checks
| Tier | Python | Postgres | React |
|---|---|---|---|
| Low | ACs implemented and tested, contract match, scope, clean lint, no silenced checks | DDL matches contract, single head, downgrade exists, verification reported | ACs and tests, contract types, API client used, clean lint and `tsc` |
| Medium | Error cases, edge cases, layering, existing callers, test quality, conventions | Safe changes to existing tables, defaults, FKs, indexes, online re-run if possible | Four UI states, error messages, double submits, test quality, shared components |
| High | Security (authn/z, object access, input, logging), performance (N+1, pagination, blocking calls), reuse, transactions | Backfills, locking, data loss, constraints on existing data, expand/contract | Security (XSS, storage), accessibility, performance (waterfalls, re-renders), reuse |

## Changes to the orchestrator package (already applied there)
- `sdlc-workflow.instructions.md`: the result contract has `verdict` and typed findings (`severity | type | file:line | issue | fix`).
- `sdlc-qa-routing`: routing by verdict and finding type, including mixed `plan-gap` and code findings, and integration-check results.
- `sdlc-delegation`: what the QA envelope contains.

## Factory status after this package
| Agent | Status |
|---|---|
| Orchestrator | built |
| Planner, Repo-Scout | built |
| Impl-{Python, Postgres, React}-{Low, Medium, High} | built |
| QA-{Python, Postgres, React}-{Low, Medium, High} | built |
| Researcher | to do |
| Jira | to do |
