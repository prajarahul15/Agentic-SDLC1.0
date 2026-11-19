# <Topic> standards (digest)

| Field | Value |
|---|---|
| Checked | <YYYY-MM-DD> |
| Built by | Researcher, run <run-id or manual> |
| Status | internal + baseline / baseline only - confirm with the engineering lead |
| Enforced by tooling | <e.g. ruff (pyproject.toml), eslint (.eslintrc.cjs) - rules already enforced are not repeated here> |

Levels: **MUST** = QA blocks the task if broken (must-fix). **SHOULD** = reported at Gate 2 (should-fix).
Origin: `[internal]` company standard · `[repo]` this repository's config or docs · `[baseline]` public reference.

## <Area 1, e.g. Error handling>
- **MUST** <rule in one line> `[internal]` (S1)
- **SHOULD** <rule in one line> `[baseline]` (S3)

## <Area 2, e.g. Logging and PII>
- **MUST** ...

## Conflicts
- <internal rule> vs <baseline rule> - internal applies.

## Sources
- S1 <title> - <url> - version <n> - checked <date>
- S2 ...

## Changes
- <YYYY-MM-DD> - first version
