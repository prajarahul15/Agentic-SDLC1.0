# Orchestrator - AI SDLC factory (iteration 1)

The Orchestrator is the entry point and supervisor of an SDLC run in VS Code with GitHub Copilot.
It coordinates the Planner, Researcher, Jira, implementer and QA agents, tracks progress and
decides routing. It never writes code.

## Approach for iteration 1: Plan B (re-invoke with memory notes)
VS Code subagents in the Local harness are stateless and cannot be resumed. So in iteration 1,
agents "stay alive" through **memory notes**: every worker returns a note of 15 lines or fewer
(key files, decisions, interfaces, gotchas). The Orchestrator keeps the latest note per task in
the run ledger and sends it with any follow-up work, so the worker doesn't need to re-read the repo.

Plan A (resuming a subagent by ID) sits behind `agent_resume.enabled` in the config. Turn it on
only if `spikes/agent-resume-test` reports RESUME WORKS on your VS Code and Copilot version.

## Files in this folder and where to install them
| File in this folder | Install in the workspace at |
|---|---|
| `agents/orchestrator.agent.md` | `.github/agents/orchestrator.agent.md` |
| `instructions/sdlc-workflow.instructions.md` | `.github/instructions/sdlc-workflow.instructions.md` |
| `skills/sdlc-task-slicing/SKILL.md` | `.github/skills/sdlc-task-slicing/SKILL.md` |
| `skills/sdlc-tier-selection/SKILL.md` | `.github/skills/sdlc-tier-selection/SKILL.md` |
| `skills/sdlc-delegation/SKILL.md` | `.github/skills/sdlc-delegation/SKILL.md` |
| `skills/sdlc-qa-routing/SKILL.md` | `.github/skills/sdlc-qa-routing/SKILL.md` |
| `skills/sdlc-run-ledger/SKILL.md` + `ledger-template.md` | `.github/skills/sdlc-run-ledger/` |
| `config/sdlc-config.yaml` | `.github/sdlc/config.yaml` |
| `config/settings.json` | merge into `.vscode/settings.json` |
| `prompts/sdlc-run.prompt.md`, `sdlc-resume.prompt.md`, `sdlc-status.prompt.md` | `.github/prompts/` |
| `spikes/agent-resume-test/*.agent.md` | `.github/agents/` (temporarily, for the test only) |

Add `.sdlc/runs/` to `.gitignore` unless you want run ledgers committed.
Commit `.sdlc/repo-map.md`, so everyone on the team reuses the same map.

## Prerequisites
- VS Code and GitHub Copilot Chat recent enough to support custom agents as subagents, skills and prompt files.
- The models named in `config.yaml` available in your Copilot model picker. Edit the names to match exactly.
- Environment variables `JIRA_BASE_URL`, `JIRA_USER`, `JIRA_API_TOKEN` (for the Jira agent).
- The worker agents: `Planner`, `Repo-Scout`, `Researcher`, `Jira`, the implementer tier variants `Impl-{Python,Postgres,React}-{Low,Medium,High}` and the QA tier variants `QA-{Python,Postgres,React}-{Low,Medium,High}`. The names must match the `agents:` list in `orchestrator.agent.md`.

## How to run
- `/sdlc-run` - start a run from a request or a Jira key.
- `/sdlc-status` - read-only status of a run.
- `/sdlc-resume` - continue an interrupted run.
Or select **Orchestrator** in the agents dropdown and describe the change.

## Run files
Each run creates exactly two files:
- `.sdlc/runs/<run-id>/plan.md` - written by the Planner.
- `.sdlc/runs/<run-id>/ledger.md` - task status, memory notes, decisions, metrics, benchmark row.

## How it stays fast, reliable and cheap
| Area | Mechanism |
|---|---|
| Cost | Sonnet only for the Orchestrator, the Planner and High-tier work; Haiku elsewhere. Repo scanning is done by Repo-Scout on Haiku, and the repo map is reused across runs. Workers return 40 lines at most. The Orchestrator never reads code. Memory notes instead of re-reading the repo. Skills load only when needed. No nested subagents except Planner → Repo-Scout. |
| Speed | Independent tasks in a wave are dispatched together. The Planner asks all its questions in one round. The Researcher runs only for flagged unknowns. |
| Reliability | Fixed task envelope and result contract. A malformed result is re-requested once. Rework limits and stop conditions. Two human gates. The ledger allows resume. Deterministic checks are run by the implementers. |

## Harness note
VS Code's Local harness (`runSubagent`) is deprecated and will be removed in February 2027.
The Copilot harness delegates with its native `task` tool, which may take different arguments.
`tools: ['agent']` covers the subagent tool set. If you switch harness, re-test delegation,
model selection for subagents and the resume test.

## Open items
- Run the resume test (half a day) and record the result.
- Confirm the exact model names available in LBG Copilot.
- Check that each tier variant runs on the model in its agent file (turn on `chat.subagents.showCreditUsage` and look at the subagent details).
- Check that the `chat.tools.terminal.autoApprove` rules are honoured in your chat permission mode. There is a reported VS Code issue where they are ignored in "Default Approvals" mode.
- Build the worker agents, starting with the Planner.
