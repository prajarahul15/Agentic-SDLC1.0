---
name: research
description: Ask the Researcher a precise technical question and get a cited answer
agent: Researcher
argument-hint: e.g. "How do we mask PII in logs?" or "Is axios 0.21.1 vulnerable?"
---

Research this question:

${input:question:Your question}

Follow the research protocol: check the repository and internal sources first, keep queries free of internal details,
state the version the answer applies to, give a confidence level, and list the sources with links.
