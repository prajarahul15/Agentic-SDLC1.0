# Planner and Repo-Scout - AI SDLC factory (iteration 1)

The **Planner** (Sonnet) turns a request into a precise, approved `plan.md`. It is precise enough that
the Orchestrator can slice it without guessing, and that low-cost implementers can follow it without
making design decisions.

**Repo-Scout** (Haiku) does the repository scanning for the Planner. It builds and refreshes a compact
repo map (`.sdlc/repo-map.md`) and answers focused "where is X and what depends on it" questions, so the
expensive model spends its tokens on design, not on reading code.

## Decisions built in
| Topic | Decision |
|---|---|
| Repo scanning | A dedicated Repo-Scout subagent, started by the Planner. The Researcher stays for external research only |
| Repo map | Kept between runs in `.sdlc/repo-map.md`, refreshed incrementally from `git diff` since the last mapped commit |
| Plan detail | File level for every change; exact signatures for anything in a contract |
| Contracts | OpenAPI snippets for REST, SQL DDL plus migration notes for the database, TypeScript interfaces for the frontend |
| Task breakdown | The Planner proposes task candidates with complexity tags; the Orchestrator finalises waves and tiers |
| New projects | The Planner chooses the structure, using the defaults in `project-scaffolding` |
| Acceptance criteria | Jira criteria are kept word for word and assessed; gaps and ambiguities become questions with a proposed default. With no Jira criteria, the Planner writes them and the user confirms them at Gate 1 |

## Files and where to install them
| File in this folder | Install in the workspace at |
|---|---|
| `agents/planner.agent.md` | `.github/agents/planner.agent.md` |
| `agents/repo-scout.agent.md` | `.github/agents/repo-scout.agent.md` |
| `skills/plan-authoring/SKILL.md` + `plan-template.md` | `.github/skills/plan-authoring/` |
| `skills/acceptance-criteria/SKILL.md` | `.github/skills/acceptance-criteria/SKILL.md` |
| `skills/contract-design/SKILL.md` | `.github/skills/contract-design/SKILL.md` |
| `skills/repo-discovery/SKILL.md` | `.github/skills/repo-discovery/SKILL.md` |
| `skills/project-scaffolding/SKILL.md` | `.github/skills/project-scaffolding/SKILL.md` |
| `skills/repo-mapping/SKILL.md` + `repo-map-template.md` | `.github/skills/repo-mapping/` |

The shared `sdlc-workflow.instructions.md`, the config and the settings come from the orchestrator package.

## Changes to the orchestrator package (already applied there)
- `settings.json`: `chat.subagents.allowInvocationsFromSubagents` is now `true`, so the Planner can start Repo-Scout. Only the Orchestrator and the Planner have the `agent` tool, so no other worker can delegate.
- `orchestrator.agent.md`: Repo-Scout added to the allowed agents (as a fallback), rule 7 allows Planner → Repo-Scout, and Phase 2 handles `repo_scan_needed`.
- `sdlc-workflow.instructions.md`: roles updated, Planner statuses noted, repo map rules added.
- `sdlc-config.yaml`: Repo-Scout model, Planner limits (questions per round, file reads) and the repo map path.
- `sdlc-delegation` skill and README: Repo-Scout rows.

## How a planning round works
1. The Orchestrator starts the Planner (`mode: draft`).
2. The Planner starts Repo-Scout `mode: map` (cheap if the map is current), then several `mode: focus` questions together.
3. The Planner reads only the files and lines it needs, assesses or writes the acceptance criteria, designs contracts, does the impact analysis, proposes task candidates and writes `plan.md`.
4. The Planner returns `NEEDS-INPUT` (questions and research needs in one batch) or `READY` with a 10-line Gate 1 summary.
5. After answers or research, the Orchestrator calls the Planner again in `revise` mode until it is `READY`.

## Fallback when nested subagents are not available
If the Planner cannot start Repo-Scout (an older VS Code version, or the setting is disabled), it returns
`repo_scan_needed`. The Orchestrator then runs Repo-Scout itself and passes the results back. Nothing else changes.

## To check in your environment
- That `chat.subagents.allowInvocationsFromSubagents` works on your VS Code and Copilot version, and with the harness you use.
- That Repo-Scout's read-only git commands (`git rev-parse`, `git ls-files`, `git diff --name-only`) run without approval prompts, or approve them once.
- Whether LBG has FastAPI or React starter templates. If so, add them to `project-scaffolding`.
