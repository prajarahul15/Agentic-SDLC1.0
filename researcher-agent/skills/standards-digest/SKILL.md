---
name: standards-digest
description: Use to build or refresh the cached standards pack (.sdlc/standards/*.md) - short, cited checklists of coding, security, database and API-design rules that implementers follow and QA checks against. Researcher only.
---

# Standards digest

Coding guidelines and security rules change rarely. Read them once, condense them into short checklists, and
let every other agent read the local file. This makes runs cheaper, faster and consistent.

## Files
| File | Content | Used by |
|---|---|---|
| `.sdlc/standards/python.md` | Python and FastAPI coding standards | Impl-Python, QA-Python, Planner |
| `.sdlc/standards/react.md` | React and TypeScript standards | Impl-React, QA-React, Planner |
| `.sdlc/standards/postgres.md` | Database naming, migration and data rules | Impl-Postgres, QA-Postgres, Planner |
| `.sdlc/standards/security.md` | Secure coding, PII and logging, auth, secrets, dependencies | All implementers, all High-tier QA |
| `.sdlc/standards/api-design.md` | REST conventions, errors, versioning, pagination | Planner, Impl-Python, QA contract checks |

Use `standards-template.md` in this folder for each file.

## Build
For each topic:
1. **Find the sources**, in this order:
   - Internal: Confluence spaces and pages in `research.internal.confluence_spaces` / `research.standards.sources`, and internal docs paths.
   - Repository: `CONTRIBUTING.md`, lint and formatter config (`ruff.toml`, `.eslintrc*`, `pyproject.toml [tool.*]`), ADRs. The tool config is the most reliable statement of what is enforced.
   - Public baseline, only for gaps: OWASP Top 10 and the relevant OWASP Cheat Sheets for security; PEP 8 / official framework docs for style.
2. **Extract rules, not essays.** Each rule is one line: what to do, a `MUST` / `SHOULD` level, and a reference.
3. **Mark the origin** of every rule: `[internal]`, `[repo]` or `[baseline]`. Internal rules win when they conflict with baseline ones; note the conflict.
4. **Keep it short:** at most 60 rules per file, grouped by area. Leave out rules the linter already enforces; say "enforced by ruff/eslint" instead.
5. Write the file with the checked date and all sources.

## Refresh
- `mode: standards` with `refresh` rebuilds files older than `research.standards.refresh_days`, or whose sources changed (Confluence version number or repo config changed).
- Keep a `## Changes` section at the end of each file: date and what changed, one line each.

## Rules for content
- Never invent a rule. If no internal source exists for a topic, build it from the repo config and public baseline only, and say at the top: "No internal standard found; baseline only - confirm with the engineering lead."
- Paraphrase; quote only where the exact wording is the rule.
- No secrets, hostnames or internal URLs other than the source links.
