---
name: build-verification
description: Use after implementing a change to run format, lint, type check and tests in the right order, classify failures, fix only what your change caused, and report checks in the result contract. All implementers.
---

# Build verification

## Order
Run the commands from the envelope's `commands` field in this order. Fix each stage before the next.
1. **Format** - apply the formatter to the files you changed (fast, removes noise for the next steps).
2. **Lint** - on the files you changed.
3. **Type check** - if the service has one.
4. **Tests** - first the tests for the area you changed (fast feedback), then the service's full test command once, if it runs in reasonable time (under about 3 minutes).

Scope commands to your files or test folder where the tool allows it, for example:
- `ruff format app/api/orders.py tests/api/test_orders.py`
- `pytest tests/api/test_orders.py -q`
- `npx vitest run src/pages/Order.test.tsx`

## Classify each failure
| Class | How to tell | Action |
|---|---|---|
| Caused by your change | Fails now, passed (or did not exist) at baseline | Fix it |
| Pre-existing | Also failed at baseline | Do not fix unless in scope. Report it |
| Environment | Missing service (database, network), missing tool, permissions | Do not work around it. Report it; return FAILED if no meaningful verification was possible |
| Flaky | Passes on a re-run with no change | Re-run once. Report it if it repeats |

## Fix loop
- At most 3 attempts per stage. Each attempt: read the error, change the smallest thing that fixes it, re-run the same command.
- Never silence a check (see the implementer protocol, rule 5).
- If it still fails after 3 attempts: stop and return FAILED, with the command, the first error lines (no more than 5) and what you tried.

## Report in the result contract
```
checks:
  ruff format --check app/api/orders.py - pass
  ruff check app/ tests/ - pass
  mypy app/ - pass
  pytest tests/api/test_orders.py -q - pass (6 tests)
  pytest -q - pass (142 tests; 1 pre-existing failure: tests/unit/test_legacy.py::test_x)
```
Never paste full logs. Summarise.
