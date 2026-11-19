---
name: sdlc-standards
description: Build or refresh the cached standards pack (.sdlc/standards) used by implementers and QA
agent: Researcher
argument-hint: Topics - python, react, postgres, security, api-design, or all
---

Run in `mode: standards` for these topics: ${input:topics:all}

Use the `standards-digest` skill. Internal standards first, then the repository's tool config, then the public baseline for gaps.
Tell me at the end which files were created or changed, which topics had no internal source (baseline only),
and any conflicts between internal and baseline rules.
