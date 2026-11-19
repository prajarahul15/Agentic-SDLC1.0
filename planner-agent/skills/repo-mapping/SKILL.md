---
name: repo-mapping
description: Use to build or refresh the compact repository map (.sdlc/repo-map.md) that other agents read instead of scanning the repo. Repo-Scout only.
---

# Repo mapping

The repo map is a flattened, compact picture of the repository: what is where, how it is organised,
and how to run it. Other agents read it instead of scanning the code.

## Build (no map yet)
1. `git rev-parse HEAD` - record as `map_commit`.
2. `git ls-files` - get the file list. Ignore generated, vendored and build output.
3. Identify the stack from manifest files: `pyproject.toml`, `requirements*.txt`, `package.json`, `alembic.ini`, `docker-compose*.yml`, CI files.
4. Identify services and components: top-level folders with their own entry point or manifest.
5. For each service, find: entry point, routers or controllers, models, migrations, tests, and the test, lint and format commands (from manifests, Makefile, CI config or README).
6. List the API surface (method, path, handler file) and the main tables (from models or migrations).
7. Note conventions with one example file each: layering, error responses, auth, logging, config.
8. Write `.sdlc/repo-map.md` from `repo-map-template.md` in this folder.

## Refresh (map exists)
1. `git diff --name-only <map_commit> HEAD`.
2. No changes in mapped areas: return "map current".
3. Otherwise update only the sections those files affect (a new route, a new table, a changed command), then update `map_commit` and the date.
4. If more than about 30% of mapped files changed, rebuild the map.

## Size and style
- 300 lines at most. Tables and short lines, not prose.
- Paths and symbol names, no code beyond one-line signatures.
- Facts only, no recommendations.
