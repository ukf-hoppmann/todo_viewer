# Scope: client

Applies to `client/**` in addition to `../architecture.md`. Derived from the
rules of `ezf-ui`, whose core is copied.

## 1. Layers and dependency direction

- Code lives in exactly one layer: `src/app` (composition root),
  `src/core`, `src/shared`, `src/plugins/<plugin-id>`.
- Allowed imports: `shared` → third-party only; `core` → `shared`;
  `plugins` → `core`, `shared`, and the public API of the plugins in its
  `requires`; `app` → `core` and plugin entry points.
- `core` MUST NOT import from any plugin. Only `src/app` knows the plugin
  list. Production code MUST NOT import test code.
- `core`, `shared`, and every plugin expose their public API only through
  the `index.ts` at their root; deep imports are forbidden. A plugin's
  `plugin.json` is read only by `src/app`.

Enforced by: ESLint rule `architecture/boundaries`
(`configs/eslint/architectureBoundaries.ts`).

## 2. Plugin contract

- Each plugin has a manifest `plugin.json` declaring `requires`, validated
  against the core's JSON schema, and exports exactly one plugin definition
  from `index.ts`: store reducer, its API (built on the core's connection),
  slot contributions, slots it provides, SSE event handlers, i18n resources.
- Importing a plugin has no side effects. Heavy parts (pages, graph layout,
  markdown rendering) are referenced through lazy imports.
- If a required plugin fails to load, the dependent plugin is inactive too;
  the app keeps running.

## 3. Navigation and slots

- Contributions to the UI of the core or another plugin happen only through
  slots, declared by their owner as `<owner-id>.<name>` with a typed shape.
- Every navigable view MUST be reachable by URL.

## 4. State

- Every store slice and every API endpoint has exactly one owner, registered
  under the owner's id. Others use only the owner's public selectors, hooks,
  and endpoints.
- Server data MUST be held by the owner's RTK Query API, not copied into
  component state. After an SSE event the owner invalidates its tags.
- `src/shared` MUST NOT hold global store state.
- Persistent UI state MUST go through the core's UI-state endpoint, not
  browser storage.

## 5. Domain logic

- Filtering, tree building, progress, dependency graph, edit rules, and due
  grouping MUST be pure functions in the owner's `domain/` folder, without
  React, DOM, or network access.

## 6. Generated code

- `src/shared/api/schema.d.ts` is generated from the server's OpenAPI
  schema and MUST NOT be edited by hand.

## 7. Test ids and tests

- Every element a UI test interacts with or reads MUST carry a stable
  `data-testid` of the form `<owner-id>.<element>`, defined as a constant by
  its owner and exported through its public API. Generated ids, CSS classes,
  visible text, and DOM position MUST NOT be used as selectors.
- Tests use Vitest and Testing Library and live under
  `tests/implementation/unit/client/` (mirroring `client/src/`).

## 8. Dependencies

- A new direct dependency in `client/package.json` MUST be approved by the
  project owner before it is installed (package, purpose, runtime or
  development). Approved with this scope: the dependencies of the copied
  `ezf-ui` core (React, React Router, Redux Toolkit, React Redux, i18next,
  react-i18next, ajv, MUI with Emotion), `@xyflow/react`, `elkjs`, `marked`,
  `dompurify`, and the development tools (Vite, TypeScript, ESLint, Vitest,
  Testing Library, jsdom, `openapi-typescript`).
