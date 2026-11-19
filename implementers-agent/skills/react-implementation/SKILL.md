---
name: react-implementation
description: Use when implementing a React/TypeScript frontend task - contract-typed API clients, components, UI states, accessibility and tests with Vitest and React Testing Library. React implementers.
---

# React and TypeScript implementation

**The repo's own conventions always win** (component style, state library, folder layout, test runner).
Look at the pattern file named in the plan before writing.

## Types and API client
- Copy the TypeScript types from the contract exactly, into the repo's types location. Field names and enum values must match the API.
- Call the backend only through the repo's API client module (one function per endpoint). Never call `fetch` or `axios` directly from components.
- No `any`. Use `unknown` and narrow it, or a precise type.
- Handle the error status codes listed in the contract (for example, 404, 409, 422) and map them to user-facing messages.

## Components
- Function components with hooks. Keep data fetching in a hook or the repo's data layer (for example React Query, if used), not inside presentational components.
- Every data-driven view handles four states: **loading**, **error**, **empty** and **success**.
- Disable submit buttons while a request is in flight, to prevent double submits.
- Reuse existing shared components (buttons, forms, tables, dialogs) instead of creating new ones.
- No hard-coded API base URLs. Use the repo's config.

## Accessibility basics
- Use semantic elements (`button`, `label`, `form`, headings) and associate labels with inputs.
- Interactive elements are reachable by keyboard.
- Images and icons that carry meaning have accessible names.

## Tests (Vitest or Jest, React Testing Library)
- At least one test per acceptance criterion that the UI covers.
- Query by role and label (`getByRole`, `getByLabelText`), not by CSS class or test IDs, unless the repo uses test IDs.
- Simulate the user with `user-event`.
- Mock the API at the boundary: MSW if the repo uses it, otherwise mock the API client module. Never call a real backend.
- The backend may not be finished when you run (parallel lanes). Your tests rely on the contract and mocks only.

## Style
- ESLint and Prettier clean, `tsc --noEmit` clean (or the repo's equivalents).
- No `console.log` left behind. No commented-out code.
