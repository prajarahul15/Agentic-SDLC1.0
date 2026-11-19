---
name: acceptance-criteria
description: Use when planning, to assess acceptance criteria that come from Jira (finding gaps and ambiguities and turning them into questions) or to write criteria when Jira has none. Planner only.
---

# Acceptance criteria

## Case 1 - Jira has acceptance criteria
1. Copy each criterion **word for word** as `AC-J1`, `AC-J2`, … Never reword a Jira criterion.
2. Assess each one against the checklist below and mark it:
   - `OK` - testable and clear.
   - `AMBIGUOUS` - more than one reasonable reading. Raise a question; your default is the reading you recommend.
   - `GAP` - something the story clearly needs is not covered. Raise a question; your default is a proposed criterion.
3. Assess the set as a whole too: anything the goal needs that no criterion covers is a `GAP`.
4. Add purely technical criteria (`AC-T…`) for things the user would not write but the code needs (for example, migration is reversible, endpoint returns 404 for an unknown ID). These do not need a question unless they change behaviour the user would notice.

## Case 2 - Jira has no acceptance criteria (or there is no Jira)
1. Write the criteria yourself as `AC-T1`, `AC-T2`, … in Given / When / Then form.
2. Cover the checklist below.
3. Do not ask a question for each one. List them in the plan; the user confirms them at Gate 1.
4. Ask a question only when the request leaves a real choice of behaviour open (for example, "should cancelled orders still be editable?").

## Checklist
| Area | Ask yourself |
|---|---|
| Happy path | Is the main outcome stated in observable terms? |
| Validation | What happens with missing, invalid or out-of-range input? |
| Not found / empty | What happens when the item does not exist, or a list is empty? |
| Permissions | Who may do this, and what happens for anyone else? |
| State rules | Which transitions or states are allowed and which are rejected? |
| Errors | What does the user or API caller see on failure (status code, message)? |
| Data integrity | What must stay true in the data (uniqueness, references, history)? |
| Non-functional | Only if the request implies it: performance, volume, audit, accessibility |
| Compatibility | Existing callers or screens that must keep working |

## Rules for a good criterion
- Observable and testable by an automated test.
- One behaviour per criterion.
- No vague words ("fast", "user-friendly", "properly", "as appropriate"). Use numbers or exact outcomes.
- Each criterion names the test that verifies it in the plan's "Verified by" column.

## Question format for gaps
`Q3 [blocking] AC-J2 says "user can update status" but not which transitions are allowed.
Options: (a) any status to any status, (b) only forward transitions, (c) a defined transition table.
Default: (b) only forward transitions; return 409 for others.`
