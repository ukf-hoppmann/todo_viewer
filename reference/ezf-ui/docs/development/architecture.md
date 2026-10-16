# Architecture rules

<!-- Binding architecture of this project. Always English; MUST, SHOULD, and
MAY have their RFC 2119 meaning. Keep this file short: rules that apply to the
whole project only. Rules for one area go into a scope file. A rule that can
be checked mechanically names its test, e.g. "Enforced by:
tests/architecture/test_layers.py". -->

## Rules

The UI mirrors the backend: a small `core` plus plugins that are switched on
or off at runtime.

### 0. Legacy code

1. `src_old` is a read-only reference. Nothing imports from it; code is
   copied and adapted, not referenced.

Enforced by: ESLint rule `architecture/boundaries`
(`configs/eslint/architectureBoundaries.ts`; tests in
`tests/implementation/unit/configs/eslint/`).

### 1. Layers and dependency direction

1. Code lives in exactly one layer: `src/app` (composition root),
   `src/core`, `src/shared`, `src/plugins/<plugin-id>`.
2. Allowed imports: `shared` → third-party only; `core` → `shared`;
   `plugins` → `core`, `shared`, and the plugins listed in its `requires`;
   `app` → `core` and plugin entry points.
3. `core` MUST NOT import from any plugin. Only `src/app` knows the plugin
   catalogue.
4. Production code MUST NOT import test code.

Enforced by: ESLint rule `architecture/boundaries` (rules 1.2–1.4; see rule
0). Imports between plugins are allowed only into the public API of plugins
listed in the importer's `plugin.json` `requires`.

### 2. Public API

1. `core`, `shared`, and every plugin expose their public API only through
   the `index.ts` at their root; a plugin's manifest `plugin.json` is read
   only by `src/app`. Deep imports into another layer or plugin are
   forbidden.

Enforced by: ESLint rule `architecture/boundaries` (see rule 0). Tests are
not production code and may import internals from `src`.

### 3. Plugin contract

1. Each plugin has a manifest `plugin.json` at its root that declares
   `requires`. It holds data only and is validated against a JSON schema of
   `core`. Each plugin exports exactly one plugin definition from its
   `index.ts`: store slices, its own API (endpoints and cache, built on the
   connection `core` provides), route and slot
   contributions, slots it provides, i18n resources, optional settings
   schema.
2. Importing a plugin has no side effects. Registration happens only through
   the definition.
3. The plugin id is the name of its folder, unique, and kebab-case.
4. The app MUST work with any plugin disabled. If a required plugin is
   inactive or fails to load, the dependent plugin is inactive too.
5. Whether a plugin is active is decided from the configuration and the
   manifests alone, before any plugin code is loaded. Plugin code is loaded
   (dynamic import) only when the plugin is active. The definition stays
   light: it references heavy parts (pages, large components) through lazy
   imports.

### 4. Navigation and slots

1. Contributions to the UI of `core` or another plugin happen only through
   slots. The owner declares a slot as `<owner-id>.<name>` with a typed
   contribution shape.
2. First navigation level: `core` main routes. Second level (sidebar):
   sub-routes of the host plugin. Every navigable view MUST be reachable by
   URL.

### 5. State ownership

1. Every global store slice and every API endpoint has exactly one owner
   (`core` or one plugin), registered under the owner's id. Others use only
   the owner's public selectors, hooks, actions, and endpoints.
2. `src/shared` MUST NOT hold global store state; it MAY provide interaction
   mechanisms (hooks, events, factories) and local component state.
3. State and endpoints used by `core` belong to `core`. A plugin that cannot
   work without another plugin lists it in `requires` and uses that plugin's
   state and endpoints through its public API. Plugins that do not depend on
   each other but share state or endpoints get them from a shared plugin they
   all require (it MAY have no UI of its own); otherwise each plugin brings
   its own. A plugin shares state and endpoints only through its public API,
   and only with plugins that list it in `requires`.

### 6. Activation

1. Active plugins are decided at runtime from configuration validated against
   a JSON schema. `core` MUST treat the source as replaceable (file now, API
   or per-user later).
2. Plugin settings live under `plugins.<id>.settings` and are validated
   against the plugin's own schema.

### 7. Test ids

1. Every element that a UI test interacts with or reads MUST carry a stable
   test id in the attribute `data-testid`. Generated ids (React `useId`, MUI
   auto ids), CSS classes, visible text, and DOM position MUST NOT be used as
   selectors.
2. A test id has the form `<owner-id>.<element>` (kebab-case parts). Its owner
   (`core` or a plugin) defines it as a constant in production code and
   exports it through its public API; tests import it from there. An element
   the owner generates for each contribution (e.g. a navigation tab) appends
   the identity of the contribution as further dot-separated parts,
   `<owner-id>.<element>.<…>`; the owner exports a function that builds these
   ids.
3. If an element a test needs has no test id, the test MUST NOT fall back to
   another selector; the missing id is added to the owner's code.
4. Exception: inside third-party components that cannot carry a test id
   (e.g. AG Grid cells), their own stable attributes (`col-id`, `data-ref`)
   MAY be used, scoped below an element with a test id.

### 8. Test tools

1. Unit and integration tests use Vitest; system tests use Selenium and
   select elements only by test id (rule 7).
2. A functional test uses Vitest for a single function and Selenium for a UI
   flow.

### 9. Dependencies

1. A new direct dependency (`dependencies` or `devDependencies` in
   `package.json`) MUST be approved by the project owner before it is
   installed. The request names the package, its purpose, and whether it is
   needed at runtime or only for development. This includes type packages
   (`@types/*`) and peer dependencies that must be installed explicitly.
2. Transitive dependencies that npm installs on its own are not covered.

## Scopes

<!-- Areas with additional rules in architecture/<Scope>.md. A scope applies
in addition to this file, never instead of it. Paths: patterns relative to
the project root in backticks, comma-separated; `*` stays within one path
part, `**` spans any number of parts. Example row:
| llm-integration | `src/llm/**`, `src/prompts/*.py` | Model calls and prompts | -->

| Scope | Paths | Covers |
|---|---|---|
| migration | `src/**`, `src_old/**`, `tests/**`, `configs/**`, `package.json` | Temporary rules for the rebuild into core and plugins |

## Inherited rules

<!-- Only in a repository with subprojects: rules of another project that
apply here as well, e.g. the core's rules for a plugin. Project: a name from
[projects] of the root config, or root. Rules in backticks: architecture.md
(that project's main rules file) or scope names of that project; an inherited
scope applies regardless of its path patterns. Nothing is inherited further.
If an inherited rule contradicts a rule of this project, this project's rule
wins and the conflict is named. Example row:
| root | `architecture.md`, `plugin-api` | -->

| Project | Rules |
|---|---|

## Changing these rules

These rules are guidelines the project owner may deliberately break. If a
requirement or design does not fit them, the AI names the conflict and
proposes solutions, and the project owner decides (skill
`claude-harness:conflicts`). A change to this file or a scope file becomes
binding only after the project owner approves it.
