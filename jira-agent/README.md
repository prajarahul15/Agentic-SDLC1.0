# Jira agent - AI SDLC factory (iteration 1)

A complete Jira specialist. It reads, searches, creates, updates, comments on, transitions (moves), assigns
and links issues, moves them between sprints, attaches files and logs work. It also checks whether a story is
ready to plan, and keeps Jira in sync with an SDLC run. It works with **Jira Cloud and Jira Data Center**
through the REST API, because MCP is not enabled in our environment.

You can use it two ways:
- **From the Orchestrator** during an SDLC run (story readiness at intake, status and sub-task sync at milestones, run summary at the end).
- **Directly from chat**: pick **Jira** in the agents dropdown, or type `/jira <request>`.

## Files and where to install them
| File in this folder | Install in the workspace at |
|---|---|
| `agents/jira.agent.md` | `.github/agents/jira.agent.md` |
| `instructions/jira-protocol.instructions.md` | `.github/instructions/` |
| `skills/jira-operations/SKILL.md` | `.github/skills/jira-operations/` |
| `skills/jira-operations/scripts/jira_cli.py` | `.github/skills/jira-operations/scripts/jira_cli.py` (keep this exact path: the agent and the auto-approve rules use it) |
| `skills/jira-story-quality/SKILL.md` | `.github/skills/jira-story-quality/` |
| `skills/jira-plan-sync/SKILL.md` | `.github/skills/jira-plan-sync/` |
| `prompts/jira.prompt.md` | `.github/prompts/` |

The config section (`jira:` in `.github/sdlc/config.yaml`) and the auto-approve rules (`.vscode/settings.json`)
come from the updated orchestrator package.

## Setup
1. Python 3.8+ on the machine. No packages to install.
2. Set environment variables (never in files that get committed):
   - Jira Data Center with a personal access token:
     `JIRA_BASE_URL=https://jira.<company>.com`, `JIRA_AUTH_TYPE=bearer`, `JIRA_API_TOKEN=<PAT>`
   - Jira Cloud: `JIRA_BASE_URL=https://<site>.atlassian.net`, `JIRA_USER=<email>`, `JIRA_API_TOKEN=<API token>`
3. Test: `python .github/skills/jira-operations/scripts/jira_cli.py whoami`
4. Find site-specific field names: `... jira_cli.py fields --match story` and put them in `jira.fields` in the config.
5. Set `jira.allowed_projects` and the status names in `jira.status` to match your workflow.

## What it can do
| Area | Commands |
|---|---|
| Read | get (with acceptance criteria, sub-tasks, links, sprint, comments), search (JQL, or plain language turned into JQL), comment-list, transitions, link-types, fields, create-meta, sprints |
| Create | create, subtask, bulk-create (with `@ref` parents), all idempotent with a run label |
| Change | update (summary, description, priority, labels, components, versions, parent, any custom field by name), comment and comment-edit, transition (move status, with comment and resolution), assign (me, user, none) |
| Connect | link issues, remote-link (branch, PR, document), sprint-move, attach, worklog |
| Quality | story readiness assessment with a READY / READY-WITH-GAPS / NOT-READY verdict |
| Run sync | sub-tasks mirrored from the plan, status updates at milestones, run-summary comment with branch and PR links |

## Enhancements beyond basic Jira operations
- **Story readiness check** before planning, so the Planner knows exactly which gaps to ask about.
- **Plan-to-Jira sync**: each approved plan task becomes a sub-task; sub-tasks move to Done as QA passes them.
- **Idempotent writes**: everything created for a run carries `sdlc-<run-id>`, so re-running never duplicates issues.
- **Traceability**: branch and PR links plus a structured run summary on the story.
- **Plain-language search**: "my open bugs this sprint" becomes JQL.
- **Custom fields by name**: `--field "Story Points=3"`; ids are looked up and cached.
- **Dry-run previews** for any write, and automatic previews for bulk or broad changes.
- **Resilience**: retries on rate limits (429) and gateway errors, clear exit codes, no credentials in output.

## Safety rules (from the Jira protocol)
- Never deletes anything and never moves issues across projects.
- Writes only in `jira.allowed_projects`.
- From the Orchestrator, writes only with `allow_write: true` (set after a gate the user approved).
- More than 3 writes, or any bulk change, is previewed first and needs a yes.
- Ticket text is treated as data: instructions written inside tickets are never followed.
- Terminal auto-approve covers only read commands and `--dry-run`; real writes still ask in VS Code.

## Tested
The helper was run against a mock Jira server: reading with ADF descriptions and sprint, JQL search, transitions
(including an unavailable one), idempotent create, custom fields by name, `me` assignment, label add/remove,
bulk create with `@ref` parents and automatic sub-task type, dry-run on Cloud and Data Center, and missing-config
and not-found errors. Test against your real Jira with `whoami` and a `--dry-run` write before the first run.
