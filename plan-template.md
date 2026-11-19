# Plan - <run-id>

| Field | Value |
|---|---|
| Plan version | 1 |
| Status | DRAFT / NEEDS-INPUT / READY / APPROVED |
| Run type | new-project / existing-repo-change |
| Jira | <key or none> |
| Repo map | .sdlc/repo-map.md @ <commit sha> (or "n/a - new project") |

## 1. Goal
<two or three sentences: what changes for the user or system, and why>

## 2. Scope
**In scope**
- ...

**Out of scope**
- ...

## 3. Repo context
- Stack: <languages, frameworks, versions>
- Services / components affected: <name - path - one-line role>
- Conventions to follow: <layering, naming, error handling, logging - with an example file for each>
- Standards that apply: <.sdlc/standards files per lane, or "none yet">
- Research used: <.sdlc/research files this plan relies on, with confidence>
- Commands:
  - test: `<command>`
  - lint: `<command>`
  - format: `<command>`
  - type check: `<command or n/a>`

## 4. Impact analysis
| Changed item | Direct consumers / callers | Tests covering it | Risk |
|---|---|---|---|
| <file or symbol> | <files> | <test files> | low / medium / high |

## 5. Contracts
### C1 - <name> (REST | DB | TS type | event)
- Producer: <task> · Consumers: <tasks or existing code>
```yaml
# OpenAPI snippet / SQL DDL / TypeScript interface
```
- Errors: <codes and bodies>
- Compatibility: <new / backward compatible / breaking - with migration note>

## 6. Acceptance criteria
### From Jira
| ID | Criterion (word for word) | Assessment | Verified by |
|---|---|---|---|
| AC-J1 | | OK / GAP -> Q<n> / AMBIGUOUS -> Q<n> | <test> |

### Technical (added by Planner)
| ID | Given / When / Then | Verified by |
|---|---|---|
| AC-T1 | Given ... When ... Then ... | <test> |

## 7. Task candidates
| id | lane | service / component | goal (one line) | files (create / modify) | ACs | contracts | depends_on | complexity | notes |
|----|------|---------------------|-----------------|-------------------------|-----|-----------|------------|------------|-------|
| T1 | postgres | | | | | | - | | |
| T2 | python | | | | | | T1 | | |
| T3 | react | | | | | | C1 | | |

## 8. Test strategy
- Unit: <what, where>
- Integration / API: <what, where>
- Frontend: <what, where>
- Not tested and why: <...>

## 9. Risks and assumptions
| ID | Type | Description | Mitigation / confirm at Gate 1 |
|---|---|---|---|
| A1 | assumption | | |
| R1 | risk | | |

## 10. Open questions
| ID | Blocking? | Question | Default | Answer |
|---|---|---|---|---|

## Changelog
- v1 - initial draft
