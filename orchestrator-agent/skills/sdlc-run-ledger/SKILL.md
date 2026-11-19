---
name: sdlc-run-ledger
description: Use to create, update, resume and close the single run ledger file that holds task status, agent memory notes, decisions and benchmark metrics for an SDLC run. Orchestrator only.
---

# Run ledger

Each run has two files, and only two:
- `.sdlc/runs/<run-id>/plan.md` - written by the Planner.
- `.sdlc/runs/<run-id>/ledger.md` - written by the Orchestrator, using `ledger-template.md` in this folder.

The ledger lets a run resume after a restart, gives each agent its memory note, and records the benchmark numbers.

## Create
Copy `ledger-template.md` to `.sdlc/runs/<run-id>/ledger.md`. Fill in the header: run ID, request, Jira key, run type, start time, and the models in use from `config.yaml`.

## Update rules
- Update after every state change: task status, routing decision, gate, question or answer.
- One line per event in the Event log. No code, diffs or full agent results.
- Replace a task's memory note when a newer one arrives. Keep only the latest.
- Count every delegation in the Delegations table.

## Resume
1. Read the ledger.
2. Rebuild the todo list from the task table.
3. Tasks marked IN-PROGRESS: treat them as not started and re-dispatch them with their memory note.
4. Continue from the first wave with a task that is not DONE.

## Close
Set the final status. Fill in the Metrics section:
- End time, duration, delegations by agent and model, rework cycles, number of questions asked, tasks DONE versus total.
- **Credits:** the agent cannot read credit usage. Ask the user to copy the figure shown in the chat (with `chat.subagents.showCreditUsage` turned on), or leave it as `to fill`.
- Add the benchmark row. The single-model baseline row is filled in by hand from the baseline run.
