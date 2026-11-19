---
name: sdlc-run
description: Start a new AI SDLC run from a request or a Jira key
agent: Orchestrator
argument-hint: Describe the change, or give a Jira key (e.g. PROJ-123)
---

Start a new SDLC run for this request:

${input:request:Describe the change, or give a Jira key}

Follow your run lifecycle from Phase 0. Create the run ledger first, then do intake and planning.
Do not start implementation until I approve the plan.
