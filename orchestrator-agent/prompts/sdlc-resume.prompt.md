---
name: sdlc-resume
description: Resume an interrupted AI SDLC run from its ledger
agent: Orchestrator
argument-hint: Run ID (folder name under .sdlc/runs)
---

Resume SDLC run `${input:runId:Run ID}`.

Read `.sdlc/runs/${input:runId}/ledger.md`, rebuild the todo list, show me a three-line status,
then continue from the first task that is not DONE. Do not repeat DONE work.
