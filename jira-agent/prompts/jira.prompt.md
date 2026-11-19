---
name: jira
description: Do something in Jira - read, search, create, update, comment, move, assign, link or check story readiness
agent: Jira
argument-hint: e.g. "show PROJ-123", "my open bugs", "move PROJ-123 to In Review", "is PROJ-140 ready to plan?"
---

Do this in Jira:

${input:request:What should I do in Jira?}

Follow the Jira protocol. If the request is broad or changes more than 3 issues, show me a preview first and wait for my yes.
Give links to every issue you mention.
