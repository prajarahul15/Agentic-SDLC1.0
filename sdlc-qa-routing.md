---
name: sdlc-qa-routing
description: Use when a QA agent or an implementer returns a result, to decide whether a task is done, needs rework, needs a plan change or must go to the user. Orchestrator only.
---

# QA routing and rework

QA returns `verdict: PASS | FAIL` and findings tagged with a severity and a type.
Only `must-fix` findings block a task. The `type` tells you where to send it.

## Decision table
| Result | Condition | Action |
|---|---|---|
| QA `PASS` | - | Task DONE. Keep `should-fix` and `nit` findings for the Gate 2 summary |
| QA `FAIL`, must-fix types are only `code`, `test`, `check` or `contract-deviation` | attempts < `max_rework_per_task` | Rework: the implementer for this lane, same task, at the same or a higher tier. The envelope includes **only the must-fix findings** and the memory note. attempts +1. Then QA again |
| QA `FAIL` with any `plan-gap` must-fix | - | Planner `mode: revise`, scope limited to that gap. Re-slice affected tasks. Tasks already DONE that consume a changed contract go back to TODO |
| QA `FAIL` with both `plan-gap` and code findings | - | Planner first. Re-dispatch the implementer only after the plan is updated, with the code findings that still apply |
| QA or implementer `BLOCKED` with a `research:` question | - | Researcher `mode: research` with that question. Send the answer back to the same agent and task. An `unverified` answer on a security rule goes to the user |
| QA `BLOCKED` | could not review (files missing, environment) | Fix the cause if you can (re-send the envelope with the correct files), otherwise ask the user |
| Implementer `FAILED` (cannot build, tests cannot pass, missing dependency) | dependency issue | Check whether the dependency task is really DONE. If not, re-order. If yes, treat as a plan gap |
| Implementer `FAILED` | other | One rework at a higher tier. If it fails again, ask the user |
| Any | attempts reached `max_rework_per_task` | Stop that task. Ask the user: retry at High tier, change the plan, or accept with known issues |

## Rules
- Never send `should-fix` or `nit` findings back for rework unless the user asks at Gate 2.
- Re-run QA after every rework, at the same tier or higher.
- If the implementer disagrees with a finding (returns BLOCKED with a reason), decide yourself if the plan answers it; otherwise ask the Planner, or the user if it is a requirement question.
- Record each routing decision in the ledger in one line: `T2 QA FAIL (2 must-fix: code, test) -> rework #1, Impl-Python-Medium`.

## Integration check results
- `PASS` -> continue to Gate 2.
- `contract-deviation` -> rework the side that deviates from the plan's contract, then run the contract check again.
- `plan-gap` -> Planner `mode: revise` for that contract, then rework the affected sides.
