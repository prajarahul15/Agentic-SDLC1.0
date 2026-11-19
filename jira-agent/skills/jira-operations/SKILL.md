---
name: jira-operations
description: Use for any Jira action - reading, searching, creating, updating, commenting, transitioning, assigning, linking, sprint moves, attachments and bulk creation - through the jira_cli.py helper (Jira Cloud or Data Center, REST API, no MCP). Jira agent only.
---

# Jira operations

All Jira access goes through the helper in this skill's `scripts` folder:
```
python .github/skills/jira-operations/scripts/jira_cli.py [--dry-run] <command> [options]
```
It needs only Python 3.8+ (standard library). It prints one line of compact JSON. Exit code 0 = success.

## Setup (environment variables)
| Variable | Jira Cloud | Jira Data Center / Server |
|---|---|---|
| `JIRA_BASE_URL` | `https://<site>.atlassian.net` | `https://jira.<company>.com` |
| `JIRA_AUTH_TYPE` | `basic` (default) | `bearer` for a personal access token, or `basic` for username + password |
| `JIRA_USER` | account email | username (basic only) |
| `JIRA_API_TOKEN` | API token | personal access token (or password) |
| `JIRA_API_VERSION` | `3` (automatic for atlassian.net) | `2` (automatic otherwise) |
| `JIRA_AC_FIELD` | optional: name of the custom field that holds acceptance criteria | same |
| `JIRA_DRY_RUN` | `1` = never send writes, only print them | same |

Cloud (v3) uses Atlassian Document Format for descriptions and comments. The helper converts text for you:
paragraphs, `#` headings, `-` bullets, `1.` numbered items and ``` code blocks. On Data Center, text is sent as written.

## Commands
### Read
| Command | Example |
|---|---|
| Who am I / test connection | `whoami` |
| One issue (AC, sub-tasks, links, sprint) | `get PROJ-123 --comments 3` |
| Search with JQL | `search "project = PROJ AND sprint in openSprints() AND assignee = currentUser()" --max 20` |
| Comments | `comment-list PROJ-123 --last 5` |
| Available transitions | `transitions PROJ-123` |
| Link types | `link-types` |
| Field names to ids | `fields --match story` (cached in `.sdlc/jira-fields.json`; `--refresh` to reload) |
| Fields needed to create | `create-meta --project PROJ --type Story` |
| Sprints on a board | `sprints --board 42 --state active,future` |

### Write
| Command | Example |
|---|---|
| Create | `create --project PROJ --type Story --summary "..." --description-file desc.md --labels sdlc,backend --priority High --assignee me --field "Story Points=3" --idempotency-label sdlc-<run-id>` |
| Sub-task | `subtask PROJ-123 --summary "T2 PATCH /orders/{id}/status" --idempotency-label sdlc-<run-id>` |
| Bulk create | `bulk-create tasks.json --project PROJ --idempotency-label sdlc-<run-id>` (always `--dry-run` first) |
| Update fields | `update PROJ-123 --summary "..." --priority Medium --components api --field "Story Points=5"` |
| Labels | `update PROJ-123 --add-label sdlc --remove-label needs-triage` |
| Change parent / epic | `update PROJ-123 --parent PROJ-100` |
| Comment | `comment PROJ-123 --body-file comment.md` |
| Edit a comment | `comment-edit PROJ-123 10042 --body "..."` |
| Move to a status | `transition PROJ-123 --to "In Review" --comment "[AI SDLC] Ready for review"` (status name or transition name) |
| Resolve | `transition PROJ-123 --to Done --resolution Done` |
| Assign | `assign PROJ-123 --user me` / `--user jane@acme.com` / `--user none` |
| Link issues | `link PROJ-123 --to PROJ-130 --type Blocks` |
| Web link (branch, PR) | `remote-link PROJ-123 --url https://github.com/org/repo/pull/7 --title "PR #7"` |
| Move to sprint | `sprint-move PROJ-123,PROJ-124 --sprint-id 311` |
| Attach a file | `attach PROJ-123 docs/plan.md` |
| Log time | `worklog PROJ-123 --time 2h --comment "Implementation"` |

Add `--dry-run` (before the command) to any write to see exactly what would be sent, without sending it.

## Bulk file format
```json
[
  {"ref": "story", "type": "Story", "summary": "Order status changes", "labels": ["sdlc"], "description": "..."},
  {"ref": "t1", "parent": "@story", "summary": "T1 Add orders.status column"},
  {"ref": "t2", "parent": "PROJ-123", "summary": "T2 PATCH /orders/{id}/status", "fields": {"Story Points": 2}}
]
```
`"parent": "@story"` points at an issue created earlier in the same file. An item with a parent and no `type` becomes a sub-task.

## Plain-language requests to JQL
| Request | JQL |
|---|---|
| my open work | `assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC` |
| current sprint of PROJ | `project = PROJ AND sprint in openSprints()` |
| bugs created this week | `project = PROJ AND type = Bug AND created >= startOfWeek()` |
| stuck in review over 3 days | `project = PROJ AND status = "In Review" AND status changed to "In Review" before -3d` |
| everything from an SDLC run | `labels = sdlc-<run-id> ORDER BY key` |
| children of an issue | `parent = PROJ-123` |

## Field handling
- Custom fields are passed by name with `--field "Name=value"`; the helper looks up the id. Numbers, JSON objects and lists are parsed automatically (`--field 'Team={"value":"Payments"}'`).
- Select-list custom fields usually need `{"value":"..."}`; user fields need the user reference; check `create-meta` when unsure.
- Story points, epic link and sprint field names differ between sites: use `fields --match <word>` to find them, and record them in config (`jira.fields`).

## Not supported (by design)
Deleting anything, moving an issue to another project, changing workflows or permissions, bulk transitions of more than 20 issues.
