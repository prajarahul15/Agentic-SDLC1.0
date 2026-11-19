---
name: research-method
description: Use to answer one precise technical question with cited sources - API contracts, library or version behaviour, internal standards, approved technology or known errors - following the source order, query hygiene, confidence rules and cache. Researcher only.
---

# Research method

## 1. Understand the question
- Restate it in one line. If it bundles several questions, split them and answer each.
- Decide the category; it decides where to look first:

| Category | Example | Look first |
|---|---|---|
| API contract | "Refund endpoint, payload and error codes of provider X" | Repo OpenAPI files, internal API catalogue, then the vendor's API reference |
| Library / version | "How do I configure an async session with SQLAlchemy 2.0.x?" | `versions`, then the official docs for that version, then the changelog |
| Coding standard | "Do we allow f-strings in log messages?" | `.sdlc/standards/`, then Confluence standards spaces |
| Security | "How must PII be masked in logs?" | `.sdlc/standards/security.md`, internal security standard, then OWASP |
| Approved technology | "Is httpx approved, or must we use requests?" | Internal approved-technology page |
| Known error | "`MissingGreenlet` in async tests" | Official docs and the library's issue tracker (allowed domains) |
| Domain term | "What is a chargeback reversal?" | Internal glossary. Always flag for human confirmation |

## 2. Check the cache first
Look in `.sdlc/research/` for an earlier answer to the same question (file names are slugs of the question).
If found, the version still matches and it is under `research.cache_days` old, return it with `cached: reused`.

## 3. Search, in source order
1. Repository: search `docs/`, `*.md`, `openapi*.y*ml`, ADRs.
2. Internal: `research_cli.py confluence-search "<terms>" --space <KEY>`, then `confluence-page <id>` for the best one or two hits.
3. Public: check each URL with `research_cli.py allowed <url>`, then fetch it with the web tool.
Stop as soon as the question is answered with `confirmed` confidence.

## 4. Query hygiene (before anything goes outside)
| Do not send | Send instead |
|---|---|
| `OrderStatusService.set_status raises InvalidTransition in lbg-orders-api` | `custom exception to 409 response FastAPI` |
| A stack trace with internal paths | The exception type and library message only |
| A Jira key, story text, customer data | The general concept |

## 5. Write the answer
- Answer the question asked, first, in plain words. Then the details the asker needs (field names, a minimal signature, the rule's exact wording).
- At most 40 lines. A short code snippet only if it is the documented usage, and say which page it comes from.
- State the version the answer applies to.
- Set the confidence level honestly, and list conflicts.

## 6. Cache it
Write `.sdlc/research/<slug-of-question>.md`:
```
# <question>
asked_by: <agent> · run: <run-id> · date: <YYYY-MM-DD> · version: <lib version or n/a>
confidence: <level>

## Answer
...

## Sources
- <title> - <url> - checked <date>
```
Never cache secrets or internal data copied from tickets.
