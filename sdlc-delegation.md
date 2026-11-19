---
name: sdlc-delegation
description: Use every time the Orchestrator starts a worker agent - building the task envelope, reusing memory notes, dispatching in parallel and validating the result contract. Orchestrator only.
---

# Delegation

## 1. Build the envelope
Use the task envelope from `sdlc-workflow.instructions.md`. Fill it from the task table and the plan:
- `goal`: one or two sentences, specific to this task.
- `files_in_scope`: from the task table. Add test files the task must create or update.
- `contract`: only the contract snippets this task produces or consumes, copied word for word.
- `acceptance`: only the criteria this task covers, with their plan numbers.
- `constraints`: coding standards to follow (name the `.sdlc/standards/<lane>.md` and `security.md` files if they exist), paths not to touch, dependencies already DONE (with one-line memory notes).
- `memory_note`: the latest note for this task, or for the same service if this is new work on it. Otherwise `none`.

**Size limit:** keep the envelope under about 60 lines. If it is longer, the task is too big: split it.

## 2. Envelopes by agent
| Agent | agent_mode | What else to include |
|---|---|---|
| Jira | `assess` / `fetch` / `sync-plan` / `sync-status` / `run-summary` (any Jira action) | Jira key, run ID, `allow_write: true` only for milestone writes the user approved at a gate. `sync-plan`: task table (id, lane, goal, ACs, files). `sync-status`: list of key -> status. `run-summary`: branch, PR URL, task counts, deferred findings, assumptions |
| Planner | `draft` / `revise` | Request, Jira summary, run type, plan path; for `revise`: user answers, research answers or QA design gap |
| Repo-Scout (fallback only) | `map` / `focus` | The scan scope or focus questions from the Planner's `repo_scan_needed` |
| Researcher | `research` / `standards` / `dependencies` | `research`: one precise question, why it matters, who asked, hints (library, version, page id). `standards`: topics. `dependencies`: optional package list. Never send code or ticket text; the Researcher must not pass them outside |
| Impl-`<Lane>`-`<Tier>` | `implement` | As above, plus `commands` from plan section 3. For rework: QA must-fix findings only, plus the previous memory note |
| QA-`<Lane>`-`<Tier>` | `review` / `contract-check` | Task goal, acceptance criteria, contract, `commands`, and the implementer's summary, files_changed, checks and assumptions. QA is read-only; do not send it the implementer's memory note unless this is a re-review |

## 3. Dispatch
- Send all READY tasks of a wave in the same turn, so the harness can run them in parallel.
- Start the tier variant agent (`Impl-Python-Medium`, `QA-React-High`, …). The model comes from that agent's file.
- Tasks in the same wave must not share files (the slicing checklist ensures this), because parallel implementers write to the same working tree.
- Count every delegation in the ledger: agent, model, task.

## 4. Validate the result
A valid result has `status`, `task_id`, `files_changed` and `memory_note`, and is under about 40 lines.
- Invalid or too long: re-request once with "Return only the result contract, under 40 lines."
- Still invalid: mark the task FAILED with reason `bad-result` and apply `sdlc-qa-routing`.
- `files_changed` lists a path outside `files_in_scope`: send it to QA with a note to check that change specifically.

## 5. Keep only what matters
After a valid result, keep in your context only: status, files_changed, checks and memory_note.
Write them to the ledger. Drop everything else.

## Memory reuse (Plan B)
Memory notes are how agents "stay alive" in iteration 1. A good note lets the next agent skip rediscovery:
```
service: orders-api
entry points: app/api/orders.py (router), app/services/order_service.py
decisions: status transitions validated in OrderService.set_status; enum in app/models/enums.py
interfaces: PATCH /orders/{id}/status  body {status}  -> 200 OrderOut | 409 invalid transition
tests: tests/api/test_orders.py::test_status_*  (run: pytest tests/api -q)
gotchas: uses async session from app/db.py; do not open a new engine
```
