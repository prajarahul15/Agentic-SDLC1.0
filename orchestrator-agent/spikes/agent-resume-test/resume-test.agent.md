---
name: Resume-Test
description: Test agent - checks whether a subagent can be resumed with its context intact (Plan A).
tools: ['agent']
agents: ['Resume-Test-Worker']
---

Run this test exactly and report the outcome.

1. Start the subagent `Resume-Test-Worker` with this task:
   "Remember the code word BLUE-HERON-42. Reply only with OK and, if the harness gives you one, your agent or session ID."
2. Note any agent ID, session ID or resume handle that the subagent tool returns.
3. If you got an ID and the subagent tool accepts a resume or ID parameter, start the same subagent again with that ID and the task:
   "What code word did I give you earlier? Reply with the word only."
   If no ID or resume parameter exists, start it again normally with the same question.
4. Report:
   - which subagent tool you used (`runSubagent`, `task` or another)
   - whether an ID was returned
   - whether a resume parameter exists
   - the second reply
   - verdict: **RESUME WORKS** only if the second reply is BLUE-HERON-42 and you did not include the word in the second task. Otherwise **NO RESUME**.
