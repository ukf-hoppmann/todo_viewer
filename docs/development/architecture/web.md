# Scope: web

Applies to `web/**` in addition to `../architecture.md`.

## 1. Structure

- `src/api/` MUST be the only place that performs HTTP requests; components
  and views use its query hooks.
- `src/api/schema.d.ts` and `src/api/openapi.json` are generated and MUST NOT
  be edited by hand.

## 2. Domain logic

- Filtering, tree building, progress, dependency graph, and edit rules MUST
  live in `src/domain/` as pure functions without React, DOM, or network
  access. `src/domain/` MAY import types from `src/api/`.
- Domain functions SHOULD have unit tests next to them (`*.test.ts`).

## 3. State

- Server data MUST be held by TanStack Query, not copied into component state.
- Persistent UI state MUST go through `src/state/` and the `/api/v2/ui-state`
  endpoint, not browser storage.

## 4. Loading

- Large libraries used by only one view (graph layout, markdown rendering)
  SHOULD be loaded on demand.
