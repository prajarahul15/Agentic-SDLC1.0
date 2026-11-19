---
name: sdlc-status
description: Show the status of an AI SDLC run without changing anything
agent: Orchestrator
argument-hint: Run ID (folder name under .sdlc/runs)
---

Read `.sdlc/runs/${input:runId:Run ID}/ledger.md` and report, without delegating or changing anything:
- status and current wave
- tasks by status (DONE / IN-PROGRESS / TODO / BLOCKED)
- open questions and assumptions
- delegations so far and rework cycles
