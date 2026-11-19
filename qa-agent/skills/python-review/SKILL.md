---
name: python-review
description: Use when reviewing a completed Python/FastAPI task - tiered checklist covering acceptance criteria, contract, tests, correctness, standards, security, performance and reuse. Python QA agents.
---

# Python review checklist

Apply the sections up to your tier. Each tier includes the ones above it.

## Low - plan conformance
- [ ] Every acceptance criterion in the envelope is implemented.
- [ ] Every acceptance criterion has at least one test, and the tests pass.
- [ ] Route path, method, status codes and response model match the contract.
- [ ] Pydantic field names, types, required flags and enum values match the contract schema.
- [ ] Only files in scope were changed (plus listed tests).
- [ ] Format and lint are clean; no silenced checks (`noqa`, `type: ignore`, skipped tests).
- [ ] No debug prints, TODOs, commented-out code or hard-coded secrets or URLs.

## Medium - correctness and standards
- [ ] Error cases from the contract are handled and return the documented codes and body shape (404, 409, 422 …).
- [ ] Edge cases: empty input, missing optional fields, boundary values, unknown IDs.
- [ ] Layering is respected: no queries in routers, no HTTP concepts in services.
- [ ] Existing callers (from the plan's impact analysis) still work; existing tests still pass.
- [ ] Tests assert the behaviour, not just the status code; they cover the failure cases the criteria mention.
- [ ] Tests are isolated: no reliance on order or leftover data; external calls are mocked.
- [ ] The repo's conventions are followed (naming, logging, settings, exception types).

## High - design, security, performance, reuse
**Security**
- [ ] Every new or changed endpoint has the right authentication and authorisation dependency.
- [ ] Object-level access is checked (a user cannot read or change another user's records by changing an ID).
- [ ] All input is validated by Pydantic or explicit checks; no raw SQL built from strings.
- [ ] No sensitive data (tokens, passwords, personal data) in logs, error messages or responses beyond the contract.

**Performance**
- [ ] No N+1 queries when returning lists with related objects.
- [ ] No unbounded queries on tables that can grow; list endpoints paginate.
- [ ] No blocking calls inside async endpoints.

**Design and reuse**
- [ ] Existing helpers, services and validators are reused rather than duplicated.
- [ ] Transactions are handled the way the repo does it; partial failures cannot leave inconsistent data.
- [ ] Money and decimal values use `Decimal`, not `float`, where relevant.
