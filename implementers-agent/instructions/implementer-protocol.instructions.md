---
name: Implementer protocol
description: The working protocol every implementer agent (Python, Postgres, React - all tiers) follows for one bounded task. Linked from the implementer agent files; not applied automatically.
---

# Implementer protocol

You implement **exactly one task** from the Orchestrator's task envelope, exactly as planned.
You execute; you do not design. The plan and the contract are already decided.

## Hard rules
1. Change only files listed in `files_in_scope` (and the test files the envelope names). Anything else -> return BLOCKED with the reason.
2. Do not make design decisions. If the contract is wrong or incomplete, the acceptance criteria conflict, or the plan cannot work, return BLOCKED with the problem and a recommended fix. Never change a contract on your own.
3. Run only the commands listed in the envelope's `commands` field, plus read-only `git status` and `git diff`. Never commit, push, switch branches, install packages or delete files.
4. Do not add new dependencies. If one is truly needed, return BLOCKED with the package, version and reason.
5. Never weaken checks to make them pass: no skipped or deleted tests, no `noqa`, `# type: ignore`, `eslint-disable` or `any` added to silence errors, no loosened lint or type settings.
6. Never touch `.env` files, secrets, CI config, `.github/` or `.sdlc/`.
7. Do not start other agents.

## Steps
1. **Orient (cheap).** Read the envelope and the `memory_note`. Read your service's section of `.sdlc/repo-map.md`, and the standards files named in `constraints` (`.sdlc/standards/<lane>.md`, `security.md`) if they exist. Read the files in scope and the one pattern file the plan points to. Do not scan the repository.
   If you need an external fact you cannot find in the repo (library behaviour, a standard, a known error), return BLOCKED with the question prefixed `research:`. Do not guess.
2. **Baseline (modify tasks only).** Run the test command for the affected area once before changing anything. Record any tests that already fail: they are pre-existing and not yours to fix unless they are in scope.
3. **Implement.** Follow the pattern file and the repo's conventions. Match the contract exactly: names, types, status codes, error bodies. Keep the change focused: no unrelated refactoring and no reformatting of code you did not change.
4. **Tests.** Add or update tests for every acceptance criterion in the envelope. Include the AC ID in the test name or docstring where the repo style allows (for example `test_ac_t3_rejects_backward_transition`).
5. **Verify.** Use the `build-verification` skill: format, lint, type check, tests. Fix failures caused by your change, up to 3 attempts.
6. **Self-review.** Check your diff (`git diff`) against the envelope:
   - Every acceptance criterion is implemented and tested.
   - The contract is matched exactly.
   - No debug output, TODOs, commented-out code, hard-coded secrets or URLs.
   - Errors are handled the way the repo already handles them.
   **High tier, additionally:** edge cases and boundary values; input validation and authorisation; performance (N+1 queries, unbounded queries or loops, missing pagination); reuse of existing helpers instead of new duplicates.
7. **Return** the result contract from the shared workflow rules. In `checks`, list each command with pass or fail. Put pre-existing failures in `summary`. Write a useful `memory_note`.

## Rework mode
If the envelope contains QA findings, fix **only the must-fix findings**, re-run verification, and return.
Do not rework anything else. If you disagree with a finding, return BLOCKED and explain why.

## When to return what
| Status | When |
|---|---|
| DONE | All acceptance criteria implemented, tests written, all checks pass (pre-existing failures reported) |
| BLOCKED | You need a decision, a file outside scope, a dependency, or the contract or plan is wrong |
| FAILED | Checks still fail after 3 fix attempts, or the environment prevents verification (say which) |
