---
name: dependency-security
description: Use to report the repository's pinned dependency versions and their known vulnerabilities (OSV database), with fixed versions, or to check a package before the Planner proposes adding it. Researcher only.
---

# Dependency security

## When
- `mode: dependencies` from the Orchestrator (for example once per run, before planning on an existing repo).
- The Planner asks "can we add package X?" or "is version Y of X safe?".
- A High-tier QA agent asks about a dependency risk.

## Steps
1. `research_cli.py versions` - list pinned versions. Only exact or caret/tilde pins can be checked; report ranges (`>=`) as "unpinned - not checked".
2. `research_cli.py osv` (or `osv --package PyPI:name==1.2.3` / `npm:name@1.2.3` for a single package).
   OSV is a public database; the request sends only package names and versions, which is allowed.
3. For each vulnerable package, report the vulnerability ids, severity, summary, and the lowest fixed version.
4. For "can we add X?": also check the internal approved-technology page (if configured) and the package's
   licence and maintenance status on its official registry page (PyPI or npm, allowed domains).

## Output
```
checked:     <n> pinned packages (<m> unpinned, not checked)
vulnerable:
  - <package> <version> (<ecosystem>) - <ids> - <severity> - fixed in <version> - <url>
recommendation: <one line per vulnerable package: upgrade to <fixed version>, or "no fix yet - flag to the user">
approval:    <for new packages: approved / not on the list / list not configured>
```

## Rules
- Never upgrade anything yourself. Report it; the Orchestrator decides whether a task is needed.
- A HIGH or CRITICAL vulnerability in a package the current change touches is flagged to the Orchestrator as a risk for Gate 1.
- Development-only dependencies are skipped unless asked (`--include-dev`).
