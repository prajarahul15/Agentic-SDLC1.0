# Implementers - AI SDLC factory (iteration 1)

Nine implementer agents: three lanes (Python, Postgres, React) times three tiers (Low, Medium, High).
Each implements **one bounded task** from the Orchestrator's task envelope, exactly as planned, and
returns a short result with a memory note. They execute; they do not design.

## Design decisions
| Topic | Decision |
|---|---|
| Tiers | Flat. The Orchestrator scores each task and starts `Impl-<Lane>-<Tier>` directly. No lane-lead agent in between (that would add an extra agent start and let a cheaper model judge its own tier) |
| "Complex" | Not a fourth tier. A task scoring 9+ (or failing at High) goes back to the Planner to be split. If it cannot be split, it runs at High and is flagged at Gate 2 |
| Models | Low and Medium: Haiku 5.5. High: Sonnet 5.5. Swap Medium to a mid-priced model if one becomes available |
| Parallelism | Postgres first when the schema changes (W1), then Python and React together (W2). With no schema change, Python and React start together. Each gets only its own slice of the plan |
| Database | Implementers verify migrations against a local database if one is reachable (upgrade -> downgrade -> upgrade). Otherwise offline: `alembic upgrade head --sql`, reported as "offline only" |
| Approvals | Safe check commands are auto-approved through `chat.tools.terminal.autoApprove`, so parallel runs do not stall. Push, reset, installs, `rm`, `curl` and `docker` always ask |
| Pre-existing failures | Recorded at a baseline run, reported, and fixed only if in scope |
| Git | Implementers never commit. The Orchestrator commits once, after Gate 2 |

## Files and where to install them
| File in this folder | Install in the workspace at |
|---|---|
| `agents/impl-python-{low,medium,high}.agent.md` | `.github/agents/` |
| `agents/impl-postgres-{low,medium,high}.agent.md` | `.github/agents/` |
| `agents/impl-react-{low,medium,high}.agent.md` | `.github/agents/` |
| `instructions/implementer-protocol.instructions.md` | `.github/instructions/` |
| `skills/build-verification/SKILL.md` | `.github/skills/build-verification/` |
| `skills/python-implementation/SKILL.md` | `.github/skills/python-implementation/` |
| `skills/postgres-migrations/SKILL.md` | `.github/skills/postgres-migrations/` |
| `skills/react-implementation/SKILL.md` | `.github/skills/react-implementation/` |

The implementer protocol has no `applyTo`, so it is not loaded into every chat. Each implementer agent links to it.

## How the pieces fit
- **Agent file (thin):** name, model, tools, and which skills to use. The only differences between tiers are the model and a short tier note.
- **Implementer protocol (shared):** hard rules, the 7-step loop (orient, baseline, implement, tests, verify, self-review, return), rework mode, and when to return DONE, BLOCKED or FAILED.
- **Lane skills:** Python (FastAPI layering, Pydantic v2, SQLAlchemy 2.x, pytest), Postgres (safe Alembic migrations, online or offline verification) and React (contract types, the four UI states, accessibility, React Testing Library).
- **build-verification:** format -> lint -> type check -> tests, failure classification, at most 3 fix attempts, and how to report checks.

## Reliability rules worth knowing
- Implementers never weaken checks to pass: no skipped tests, no `noqa` or `eslint-disable`, no `any`.
- They change only the files in scope, add no dependencies, and never touch `.env`, `.github/`, `.sdlc/` or CI config.
- If the plan or contract is wrong, they return BLOCKED with a recommended fix. They never redesign.

## Changes to the orchestrator package (already applied there)
- `orchestrator.agent.md`: `agents:` lists all 18 tier variants (9 implementers and 9 QA), the worker table explains the naming, complex tasks go back to the Planner, and dispatch names `Impl-<Lane>-<Tier>`.
- `sdlc-tier-selection`: the "Complex" rule, updated Postgres floors, and the variant-based dispatch.
- `sdlc-workflow.instructions.md`: the task envelope has a new `commands` field.
- `sdlc-delegation`, `sdlc-task-slicing`, `sdlc-config.yaml`, `settings.json` (terminal auto-approve and protected edits) and the README.

## To check in your environment
- Exact model names in your Copilot picker (edit each agent file's `model`).
- That the terminal auto-approve rules are honoured in your chat permission mode.
- Whether a local Postgres is available to agents for online migration checks.
