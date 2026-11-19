---
name: jira-plan-sync
description: Use to keep Jira in step with an SDLC run - mirror approved plan tasks as sub-tasks, move the story and sub-tasks through statuses at run milestones, add branch and PR links, and post run summaries. Jira agent only.
---

# Jira plan sync

The Orchestrator calls these actions at run milestones. Each is idempotent: running it twice changes nothing
the second time. All issues the factory creates carry the label `sdlc-<run-id>`.

Status names come from `jira.status` in `.github/sdlc/config.yaml`, for example:
`start: In Progress`, `review: In Review`, `done: Done`, `blocked: Blocked`.

## `sync-plan` (after Gate 1, only if `jira.sync_subtasks: true`)
Input from the envelope: story key, run ID, and the approved task table (id, lane, goal).
1. Build a bulk file: one sub-task per task, `summary = "<task id> <goal>"`, labels `sdlc`, `sdlc-<run-id>`, `lane-<lane>`, and a description listing the task's acceptance criteria IDs and files.
2. `--dry-run bulk-create` and check the preview. If more than `jira.max_subtasks` (default 15), return NEEDS-CONFIRM.
3. `bulk-create <file> --idempotency-label sdlc-<run-id>`.
4. Return the mapping `task id -> sub-task key`. The Orchestrator stores it in the ledger.

## `sync-status` (at milestones)
| Milestone | Story | Sub-tasks |
|---|---|---|
| Gate 1 approved | -> `status.start` | - |
| Task DONE (QA PASS) | - | that sub-task -> `status.done` |
| Task stopped (rework limit) | - | that sub-task -> `status.blocked` (if the workflow has it), plus a comment with the reason |
| Gate 2 approved and pushed | -> `status.review` | - |
Before each transition, list transitions. If the target is not reachable in one step, return BLOCKED with the
available transitions; never chain several transitions without being told the path.

## `run-summary` (after push)
1. `remote-link <story> --url <branch or PR url> --title "Branch <name>"` (or the PR).
2. `comment <story> --body-file summary.md` with:
```
[AI SDLC] Run <run-id> completed
Branch: <branch>   PR: <url or "not created">
Tasks: <done>/<total> done, <rework cycles> rework cycles
Acceptance criteria: <AC ids> implemented and tested
Deferred (should-fix): <count, one line each, at most 5>
Assumptions to confirm: <list or "none">
```
3. Optional (`jira.log_work: true`): `worklog <story> --time <run duration rounded to 15m> --comment "AI SDLC run <run-id>"`.

Keep comments factual and short. Never paste code or full logs into Jira.
