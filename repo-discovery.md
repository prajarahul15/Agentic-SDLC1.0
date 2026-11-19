---
name: repo-discovery
description: Use when planning a change to an existing repository - getting the repo map, asking Repo-Scout focused questions, reading only what is needed, and doing the impact analysis. Planner only.
---

# Repo discovery (Planner side)

Goal: understand exactly the part of the repo this change touches, at the lowest cost.
Repo-Scout (low-cost model) does the scanning; you do the thinking.

## Steps
1. **Repo map.** Check `.sdlc/repo-map.md`.
   - Missing: start Repo-Scout with `mode: map`.
   - Present: start Repo-Scout with `mode: map` anyway. It returns "map current" cheaply if nothing changed, or refreshes only what changed.
   - Read the map. It gives you the stack, services, conventions and commands.
2. **Focused questions.** From the request and the map, list what you need to know, then start Repo-Scout with `mode: focus` for each. Send independent questions together. Good focus questions:
   - "Where are order status changes handled, and what calls that code?"
   - "Which tests cover the orders API, and how are they run?"
   - "Which React components call the orders endpoints?"
   - "How do existing endpoints return validation and not-found errors? Give one example file."
3. **Targeted reading.** Read only the files and line ranges Repo-Scout pointed to that you need for design decisions, up to `limits.planner_max_file_reads`. Prefer reading one example of a pattern over reading every instance.
4. **Impact analysis.** For every file or symbol the plan changes, record:
   - direct callers and consumers (from Repo-Scout's "depended on by")
   - tests that cover it
   - risk: `high` if it is shared, public, money- or auth-related, or untested
   Put this in section 4 of the plan.
5. **Repo context.** Fill section 3 of the plan from the map: stack, affected services, conventions with an example file each, and the test, lint, format and type-check commands.
   If `.sdlc/standards/` exists, list the standards files that apply to each lane, and design within their MUST rules (for example, the error format in `api-design.md`).
   Unknowns about standards, library versions or external APIs go to `research_needed`; check `.sdlc/research/` first for earlier answers.

## Fallback
If you cannot start Repo-Scout (subagent nesting is off in this environment), return `NEEDS-INPUT` with
`repo_scan_needed` listing the map refresh and the focus questions. The Orchestrator runs Repo-Scout and
passes the results back in `revise` mode.
