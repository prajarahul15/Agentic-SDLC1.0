---
name: react-review
description: Use when reviewing a completed React/TypeScript task - tiered checklist covering acceptance criteria, contract types, UI states, tests, accessibility, security, performance and reuse. React QA agents.
---

# React review checklist

Apply the sections up to your tier. Each tier includes the ones above it.

## Low - plan conformance
- [ ] Every acceptance criterion the UI covers is implemented and has a test; the tests pass.
- [ ] TypeScript types match the contract exactly (field names, optionality, enum values).
- [ ] The backend is called only through the repo's API client, with the contract's path and method.
- [ ] Only files in scope were changed (plus listed tests).
- [ ] ESLint, Prettier and `tsc --noEmit` clean; no `any`, `eslint-disable` or `@ts-ignore` added; no skipped tests.
- [ ] No `console.log`, commented-out code or hard-coded URLs.

## Medium - correctness and standards
- [ ] Loading, error, empty and success states are all handled for data-driven views.
- [ ] The contract's error codes (404, 409, 422 …) produce clear user-facing messages.
- [ ] Submit actions are disabled while a request is in flight; no double submits.
- [ ] Tests query by role or label, simulate the user with `user-event`, and mock the API at the boundary.
- [ ] Components that were changed still work on the other screens that use them.
- [ ] The repo's conventions are followed (component structure, hooks, state library, styling).

## High - design, security, accessibility, performance, reuse
**Security**
- [ ] No `dangerouslySetInnerHTML` with data that is not sanitised.
- [ ] No tokens or personal data stored in `localStorage` or logged, unless the repo already does this by design.
- [ ] UI hides actions the user is not allowed to take, and still relies on the backend for enforcement.

**Accessibility**
- [ ] Semantic elements; labels are associated with inputs; everything is reachable by keyboard; meaningful icons have accessible names.

**Performance**
- [ ] No request waterfalls that could run in parallel; no refetching on every render.
- [ ] No unnecessary re-renders from new objects or functions created in render for memoised children (only where it matters).

**Design and reuse**
- [ ] Shared components and hooks are reused, not duplicated.
- [ ] Data fetching sits in hooks or the data layer, not in presentational components.
