---
name: SDLC workflow rules
description: Shared rules for every agent in the AI SDLC factory - roles, task envelope, result contract, clarification, context budget and safety.
applyTo: '**'
---

# SDLC workflow - shared rules for all agents

## Roles
- **Orchestrator** coordinates, tracks and decides routing. It is the only agent that talks to the user, and it starts every other agent, with one exception below.
- **Planner** produces the plan. It may start **Repo-Scout** (and only Repo-Scout) to map and query the repository.
- **Repo-Scout** maps the repository and answers focused "where is X" questions. **Researcher** answers external unknowns (web, approved sites). **Jira** reads and updates Jira.
- **Implementers** carry out one bounded task. **QA agents** review one completed task.

## Flow
Intake -> Plan (with research and user questions) -> Gate 1: plan approval -> Slice into tasks
-> Implement in dependency waves -> QA each task -> Integration check -> Gate 2: final review -> Commit, push, Jira update.

## Task envelope (what a worker receives)
Every delegation has these fields and nothing else:
```
run_id:          <id>
task_id:         <e.g. T3>
agent_mode:      <implement | review | contract-check | draft | revise | fetch | comment | research>
tier:            <low | medium | high>         (implementers and QA only)
goal:            <one or two sentences>
files_in_scope:  <paths the worker may read and change>
contract:        <only the interface snippet this task needs>
acceptance:      <numbered, testable criteria>
constraints:     <standards, do-not-touch paths, dependencies already done>
commands:        <implementers and QA: the exact format, lint, type-check, test and migration commands from the plan>
allow_write:     <Jira only: true when the user approved this milestone at a gate; otherwise omit (read-only)>
memory_note:     <previous note for this task or service, or "none">
return:          result contract
```

## Result contract (what a worker returns)
Return exactly this block and nothing else. Keep the whole result under 40 lines.
```
status:        DONE | BLOCKED | FAILED
task_id:       <id>
summary:       <what was done, at most 3 lines>
files_changed: <path - one-line purpose, one per line>
checks:        <command - pass|fail, e.g. "pytest tests/api - pass">
verdict:       <QA only: PASS | FAIL>   FAIL if any must-fix finding
findings:      <QA only: severity | type | file:line | issue | fix>
               severity = must-fix | should-fix | nit
               type     = code | test | check | contract-deviation | plan-gap
questions:     <numbered, each with a recommended default, or "none">
assumptions:   <each assumption made, or "none">
memory_note:   <15 lines at most: key files, decisions, interfaces, gotchas, for the next agent working on this>
```
Do not paste source code, full diffs or full logs into a result. Point to the file and line.

The Planner uses its own statuses (`NEEDS-INPUT` | `READY` | `BLOCKED`) and extra fields, defined in its agent file.

## Shared repository knowledge
- `.sdlc/repo-map.md` is the compact map of the repository, maintained by Repo-Scout. Read it before searching the code.
- `.sdlc/standards/*.md` is the standards pack (coding, security, database, API design), maintained by the Researcher. If the file for your lane exists, its MUST rules are mandatory and its SHOULD rules are expected.
- `.sdlc/research/*.md` holds earlier research answers with sources. Check it before asking for new research.
- Never edit the repo map unless you are Repo-Scout. Never edit `.sdlc/standards/` or `.sdlc/research/` unless you are the Researcher.
- Need an external fact (library behaviour, standard, known error) to continue? Return BLOCKED with the question prefixed `research:`. Never guess.

## Clarification
- Never invent an answer to a question you were asked to resolve, and never treat silence as approval.
- If you cannot continue without an answer, return `status: BLOCKED` with the question and a recommended default.
- If you continue on an assumption, list it under `assumptions`. The Orchestrator shows every assumption at Gate 2.

## Context budget
- Read only the files in `files_in_scope` plus the files they import directly. Do not scan the whole repository.
- Use search to find the code you need, then read only the relevant parts.
- Prefer the memory note over rediscovering code you or another agent already worked on.
- Load a skill only when the task needs it.

## Safety
- Never write secrets, tokens or credentials into files, prompts or results. Jira and Git credentials come from environment variables.
- Never run destructive commands (dropping data, `rm -rf`, force-push, resetting history) unless the task envelope explicitly allows it after a user approval.
- Stay inside `files_in_scope`. If a change outside it is needed, return BLOCKED and explain why.
