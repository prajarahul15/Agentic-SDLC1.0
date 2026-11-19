---
name: jira-story-quality
description: Use to assess whether a Jira story is ready for planning - summary, user value, acceptance criteria, scope, dependencies and open questions - and return a readiness verdict the Planner can act on. Jira agent only.
---

# Story readiness assessment

Run this for `action: assess`, or at intake when the Orchestrator asks for it. It is read-only.
You report what the ticket contains and what is missing. The Planner decides what to ask the user.

## Steps
1. `get <KEY> --comments 5` (and the acceptance-criteria custom field if configured).
2. If the story has linked or child issues that look relevant (blocks, is blocked by, sub-tasks), list them with their status. Do not fetch more than 5 linked issues.
3. Score the checklist below.
4. Return the story (acceptance criteria word for word) plus the readiness table.

## Checklist
| # | Check | Pass when |
|---|---|---|
| 1 | Clear summary | One specific change, not a theme ("Allow customers to cancel an unpaid order", not "Orders improvements") |
| 2 | User value | The description says who benefits and why (a user story sentence or equivalent) |
| 3 | Acceptance criteria present | At least one criterion, in the description or the AC field |
| 4 | Criteria testable | Each criterion has an observable outcome; no vague words ("fast", "properly", "user-friendly") |
| 5 | Error and edge cases | At least one criterion covers a failure, validation or permission case |
| 6 | Scope bounded | Fits one story; no "and also" lists of unrelated changes |
| 7 | Dependencies known | Blocking links are listed and their status known |
| 8 | No open questions | Comments contain no unanswered questions to the product owner |
| 9 | Technical context | Component, service or affected area named (component field, labels or text) |

## Verdict
| Verdict | When |
|---|---|
| `READY` | Checks 1, 3 and 4 pass, and no more than two others fail |
| `READY-WITH-GAPS` | Checks 1 and 3 pass, but some criteria are vague or edge cases are missing; the Planner will raise questions |
| `NOT-READY` | No acceptance criteria, an unclear summary, an unresolved blocker, or open questions in comments |

## Output
```
story:
  key / summary / type / status / priority / url
  acceptance_criteria: <verbatim, numbered as in the ticket>
  linked: <key - relation - status>
readiness:
  verdict: READY | READY-WITH-GAPS | NOT-READY
  checks: <#  pass|fail  one-line reason>
  gaps:   <what is missing, phrased as questions the Planner can ask>
```
Never invent acceptance criteria here. Proposing criteria is the Planner's job.
