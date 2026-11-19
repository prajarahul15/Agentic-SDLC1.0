---
name: contract-check
description: Use for the integration check after all lanes are done - verify that every consumer uses each contract exactly as the producer implemented it (API paths, payloads, status codes, types, schema). High-tier QA agents in contract-check mode.
---

# Contract check (integration)

Each lane's QA has checked its own task. You check that the lanes fit together.

## Input (from the envelope)
- The contracts from the plan (C1, C2, …).
- The `files_changed` of every lane.
- The commands for each lane.

## For each contract
| Check | Producer side | Consumer side |
|---|---|---|
| Path and method | Router path and method | API client function path and method |
| Request body | Pydantic request schema | TypeScript type sent |
| Response body | `response_model` | TypeScript type read |
| Field names and casing | Pydantic aliases or serialisation settings | Property names used |
| Enums | Allowed values | Union type values |
| Status codes | Codes actually raised | Codes the UI handles |
| Database | Migration columns and types | ORM model fields and the queries that use them |

## How
1. For each contract, open the producer file and the consumer file side by side (from `files_changed`). Compare field by field.
2. Watch for the common mismatches: snake_case versus camelCase without an alias, optional versus required, `null` versus missing, integer versus string IDs, date formats, enum spelling, unhandled error codes.
3. If both backend and frontend test suites can run, run each lane's test command once.
4. Do not review code quality again. Only report contract mismatches.

## Findings
- Producer and consumer differ, and one side matches the plan's contract: `must-fix | contract-deviation` on the side that deviates.
- Both sides agree with each other but differ from the plan, or the contract itself is ambiguous: `must-fix | plan-gap`.
- Verdict `PASS` only if every contract matches on both sides.
