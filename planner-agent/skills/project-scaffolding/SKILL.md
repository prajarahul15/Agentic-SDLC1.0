---
name: project-scaffolding
description: Use when planning a new project (no existing repo) to choose the project structure, tooling and commands for Python/FastAPI, PostgreSQL and React/TypeScript. Planner only.
---

# Project scaffolding for new projects

For iteration 1 the Planner chooses the structure, using these defaults. If the request or an LBG
template says otherwise, follow that and record the decision in the plan.

## Backend - Python / FastAPI
```
backend/
  app/
    main.py              # FastAPI app, router registration
    core/config.py       # settings via pydantic-settings, read from environment
    api/routers/         # one module per resource
    schemas/             # Pydantic request/response models (match the contracts)
    services/            # business logic
    repositories/        # data access
    models/              # SQLAlchemy 2.x ORM models
    db/session.py        # engine and session
  migrations/            # Alembic
  tests/
    unit/
    api/                 # httpx TestClient tests
  pyproject.toml
  .env.example
```
- Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, pytest, httpx.
- Lint and format: ruff (`ruff check .`, `ruff format .`). Type check: mypy (optional for iteration 1).
- Commands: test `pytest -q`, lint `ruff check .`, format `ruff format --check .`.

## Database - PostgreSQL
- Migrations with Alembic, one migration per task, with a working downgrade.
- Naming: snake_case tables (plural) and columns; `id` primary keys; `created_at`, `updated_at` timestamps.
- Local database through `docker-compose.yml` (Postgres service only) and `DATABASE_URL` in `.env.example`.

## Frontend - React / TypeScript
```
frontend/
  src/
    api/                 # typed API client, one module per resource
    types/               # TypeScript types mirroring the API contracts
    components/
    pages/
    hooks/
    App.tsx
    main.tsx
  tests/ (or *.test.tsx next to components)
  package.json
  vite.config.ts
```
- Vite, React, TypeScript (strict), Vitest, React Testing Library, ESLint, Prettier.
- Commands: test `npm test -- --run`, lint `npm run lint`, format `npx prettier --check .`, type check `npx tsc --noEmit`.

## Root
- `README.md` with setup and run steps, `.gitignore`, `.env.example` (no real secrets), `docker-compose.yml` for the database.

## In the plan
- Put the chosen structure and commands in section 3 (Repo context).
- Make the scaffold its own first task (wave W0) per lane: backend skeleton, frontend skeleton, database and migrations setup.
- Later tasks then follow the scaffold's patterns.
