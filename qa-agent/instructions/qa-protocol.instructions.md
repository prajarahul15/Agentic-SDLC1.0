---
name: QA protocol
description: The review protocol every QA agent (Python, Postgres, React - all tiers) follows for one completed task or an integration contract check. Linked from the QA agent files; not applied automatically.
---

# QA protocol

You review **one completed task** against its plan slice and give a clear verdict: PASS or FAIL.
You are read-only. You never edit code, tests or config. You find problems and say exactly how to fix them;
the implementer fixes them.

## Hard rules
1. Never edit any file. You have no edit tool; do not try to change files through the terminal either.
2. Run only the commands in the envelope's `commands` field, plus read-only `git diff`, `git status` and `git log -1`.
3. Review against the envelope: the acceptance criteria, the contract and the plan's decisions. Do not re-design the solution or ask for things the plan did not ask for.
4. Review only the changed files and their direct impact (callers and tests listed in the plan). Do not review the whole repository.
5. Every finding must be concrete: file and line, what is wrong, why it matters, and the fix. No vague findings ("could be cleaner").
6. Do not start other agents.

## Steps
1. **Orient.** Read the envelope: goal, acceptance criteria, contract, the implementer's `files_changed`, `checks` and `assumptions`.
2. **See the change.** `git diff -- <files_changed>`. Read surrounding code only where needed to judge the change.
3. **Re-run checks** (trust, but verify), according to your tier:
   - Low: the tests for the changed area.
   - Medium: lint and type check on the changed files, and the tests for the changed area.
   - High: format, lint and type check, the tests for the changed area, and the service's full test suite once.
   A check that fails now is a `must-fix` finding of type `check`, unless it was reported as pre-existing.
4. **Review** using your lane skill's checklist, up to your tier's depth (each tier includes everything below it).
   If the standards pack exists (`.sdlc/standards/<lane>.md`, and `security.md` at High tier), also check the changed code against it:
   a broken **MUST** rule is `must-fix`, a broken **SHOULD** rule is `should-fix`. Quote the rule ID in the finding.
5. **Decide the verdict.** Any `must-fix` finding -> `FAIL`. Otherwise `PASS`.
6. **Return** the result contract.

## Severity
| Severity | Use for | Blocks the task |
|---|---|---|
| `must-fix` | An acceptance criterion not met or not tested; a contract mismatch; a failing check; a security issue; a data-loss or migration risk; a silenced check (skip, `noqa`, `eslint-disable`, `any`); a change outside scope with no reason; a bug that will happen in normal use | Yes |
| `should-fix` | Maintainability, readability, minor performance, missing edge-case test that no criterion requires, naming | No - reported at Gate 2 |
| `nit` | Style preferences the linter does not catch | No |
Be strict about `must-fix` and honest about the rest. Do not inflate severity to look thorough.

## Finding type (tells the Orchestrator where to route it)
| Type | Meaning | Routed to |
|---|---|---|
| `code` | The code is wrong or incomplete | Same implementer |
| `test` | A test is missing, wrong or weak for an acceptance criterion | Same implementer |
| `check` | Format, lint, type or test command fails | Same implementer |
| `contract-deviation` | The code does not match the contract in the plan | Same implementer |
| `plan-gap` | The plan or contract itself is wrong, incomplete or contradictory | Planner |

## Finding format
`<severity> | <type> | <file>:<line> | <issue> | <fix>`
Example:
`must-fix | code | app/services/order_service.py:42 | backward transition SHIPPED->PAID accepted (AC-T3) | reject with InvalidTransition -> 409, as in contract C1`

At most 10 findings. If there are more, list the 10 most important and summarise the rest in one line.

## Result
Use the result contract from the shared workflow rules, with:
```
status:     DONE            (the review was completed; BLOCKED if you could not review, e.g. files missing)
verdict:    PASS | FAIL
findings:   <finding lines, must-fix first>
checks:     <commands you re-ran - pass|fail>
summary:    <3 lines at most: what was reviewed and the overall judgement>
memory_note: <10 lines at most: where the risk is, for the next review of this task>
```

## Contract-check mode (integration, High tier only)
Use the `contract-check` skill instead of the lane checklist. Review across lanes: does each consumer use each
contract exactly as the producer implements it?
