---
name: python-implementation
description: Use when implementing a Python backend task (FastAPI, Pydantic, SQLAlchemy, pytest, ruff) - layering, contract matching, error handling and test patterns. Python implementers.
---

# Python implementation

**The repo's own conventions always win.** Use these defaults only where the repo has no pattern.
Before writing, look at the pattern file named in the plan.

## Layering (FastAPI)
| Layer | Responsibility | Must not |
|---|---|---|
| Router (`api/routers/`) | HTTP: path, method, status codes, dependencies, response model | Contain business rules or queries |
| Schemas (`schemas/`) | Pydantic request and response models, matching the contract exactly | Contain logic |
| Service (`services/`) | Business rules, transitions, orchestration of repositories | Know about HTTP |
| Repository (`repositories/`) | Database queries | Contain business rules |
| Model (`models/`) | SQLAlchemy ORM mapping | Contain business rules |

## Contract matching
- Route path, method and status codes exactly as in the contract snippet.
- Pydantic field names, types, required or optional, and enum values exactly as in the schema.
- `response_model` set on every route.
- Error responses: raise the repo's existing exception types (or `HTTPException`) with the status codes and body shape in the contract.

## Pydantic v2 and SQLAlchemy 2.x
- `model_config = ConfigDict(from_attributes=True)` for response models built from ORM objects.
- Use `Annotated` and `Field` for constraints (`min_length`, `ge`, …) so validation errors come from Pydantic.
- SQLAlchemy 2.x style: `select(...)`, `session.execute(...)`, `Mapped[...]` and `mapped_column(...)`.
- Use the session dependency the repo already has. Never create a new engine or session factory.
- Avoid N+1: use `selectinload` or `joinedload` where you return related objects in a list.
- Paginate any list endpoint that can grow, using the repo's pagination pattern.

## Configuration and secrets
- Read settings from the existing settings object. Never hard-code URLs, credentials or environment-specific values.
- If a new setting is needed, add it to the settings class and to `.env.example`, if those files are in scope; otherwise return BLOCKED.

## Tests (pytest)
- API tests with the repo's test client fixture (httpx or FastAPI `TestClient`).
- One test per acceptance criterion as a minimum: the happy path, plus validation errors, not found and permission cases where the criteria cover them.
- Unit-test service logic (for example, state transitions) without HTTP.
- Use existing fixtures and factories. Mock external calls (HTTP, queues) at the boundary. Never call real external services.
- Tests must not depend on execution order or on data left by other tests.

## Style
- Type hints on every new function. Docstrings only where the repo uses them.
- Logging through the repo's logger. Never log secrets or personal data.
- `ruff format` and `ruff check` clean (or the repo's formatter and linter).
