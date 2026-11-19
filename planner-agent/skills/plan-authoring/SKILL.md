---
name: plan-authoring
description: Use when writing or revising plan.md for an SDLC run - the required structure, level of detail and the self-check that must pass before the plan is READY. Planner only.
---

# Plan authoring

Write `plan.md` from `plan-template.md` in this folder. The Orchestrator's task-slicing skill relies on
these section names and IDs, so keep them exactly.

## Level of detail
- **File level for all changes:** which files are created or modified, and what changes in each, in one or two lines.
- **Exact signatures for anything in a contract:** endpoint, request and response schemas, error codes, table columns and types, shared TypeScript types.
- **No implementation code** beyond signatures and contract snippets. The plan says *what* and *where*, precisely. Implementers write the *how*.
- Use the repo's existing names, patterns and folders (from the repo map). Point to an existing file to copy the pattern from when one exists: "follow the pattern in `app/api/customers.py`".

## IDs
- Contracts: `C1`, `C2`, …
- Acceptance criteria: `AC-J1`… (from Jira, word for word) and `AC-T1`… (technical, added by the Planner).
- Task candidates: `T1`, `T2`, …
- Questions: `Q1`, … ; assumptions: `A1`, …

## Complexity tag per task candidate
- `low`: new code in one place, following an existing pattern, no shared interfaces.
- `medium`: changes existing behaviour, or touches 3+ files, or needs new tests around existing code.
- `high`: auth, money or payment logic, PII, concurrency, a migration on existing data, a change to a shared library or public contract, or no clear pattern to follow.

## Self-check (all must pass before `READY`)
- [ ] Every acceptance criterion is testable and mapped to at least one task and one test.
- [ ] Every Jira criterion was assessed; every gap became a question or a technical criterion.
- [ ] Every contract has a producing task, and a consuming task if used across lanes.
- [ ] Every file listed as "modify" exists in the repo map or was confirmed by Repo-Scout.
- [ ] Each task candidate touches 8 files at most and belongs to one lane.
- [ ] Dependencies point only to earlier work, and shared-library changes come first.
- [ ] Test, lint and format commands are listed.
- [ ] No vague words: "appropriate", "as needed", "etc.", "handle properly", "and so on".
- [ ] Every assumption is listed and every blocking question is in the result.
If any item fails and you cannot fix it, return `NEEDS-INPUT` and say which item.
