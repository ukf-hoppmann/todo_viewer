# Architecture rules

<!-- Binding architecture of this project. Always English; MUST, SHOULD, and
MAY have their RFC 2119 meaning. Keep this file short: rules that apply to the
whole project only. Rules for one area go into a scope file. A rule that can
be checked mechanically names its test, e.g. "Enforced by:
tests/architecture/test_layers.py". -->

## Rules

The viewer is being rebuilt (`EPIC-007`, design in
`docs/todo/items/EPIC-007/EPIC-007_spec.md`). The new code lives in
`server/` and `client/`. Sections 1–5 apply to the new code. The old viewer
in `src_old/backend/` and `src_old/web/` follows the scopes `legacy`,
`backend`, and `web` until it is removed after the owner has accepted the
rebuild (`STORY-084`).

### 0. Reference code

- `src_old/` (the old viewer) and `reference/` (snapshots of other projects,
  currently `reference/ezf-ui/`) are read-only references for the rebuild.
  New code MUST NOT import from them; code is copied and adapted. Enforced
  by: `server/pyproject.toml` (`[tool.importlinter]`) and the ESLint rule
  `architecture/boundaries` (created with `STORY-061` and `STORY-066`).
- `src_old/` MUST keep building and running the old viewer until the
  cutover; it is changed only to keep it running.
- `src_old/` and `reference/` MUST NOT be deleted before the project owner
  has accepted the rebuild.

### 1. Core and plugins

- The application MUST consist of a core without domain logic and plugins
  that carry the domain logic. A plugin has a backend part
  (`server/src/viewer/plugins/<id>/`) and a frontend part
  (`client/src/plugins/<id>/`) with the same kebab-case id (`_` instead of
  `-` in the Python package name); either part MAY be missing.
- The core MUST NOT import any plugin. A plugin MUST import only the core,
  shared code, and the public interface of the plugins listed in its
  `requires`. Enforced by: `server/pyproject.toml` (`[tool.importlinter]`)
  and the ESLint rule `architecture/boundaries`
  (`client/configs/eslint/architectureBoundaries.ts`).
- Only the composition roots (`server/src/viewer/app/composition.py`,
  `client/src/app/`) know the plugins. The active plugins MUST be a fixed list
  in code there; plugins are wired there by constructor injection.
- A plugin MUST NOT write HTTP routes or MCP tools by hand. It declares
  operations; the core publishes each operation as an HTTP route and, unless
  excluded, as an MCP tool.
- Plugins that do not require each other MUST communicate only through core
  events.
- Behaviour needed by more than one plugin MUST live in the core or in
  `client/src/shared`, not be copied between plugins.
  Why: reuse is a design goal; a new plugin should mostly configure existing
  building blocks.

### 2. Storage

- The database MUST be the single source of truth. A project MAY keep a
  markdown mirror. Ordinary requests read and write only the database; the
  mirror is read and written only by the sync.
- There MUST be exactly two storage infrastructures in the core: database
  and files. A plugin that is mirrored provides a codec (files ⇄ entries) and
  a sync participant (database ⇄ entries). The sync is a use case of the core
  over these ports and MUST NOT know SQL, file formats, or plugin domains.
- Entries MUST be matched by their `uid` only. Labels (`STORY-012`,
  `NOTE-003`) are for display, are assigned only by the database, are counted
  per project and prefix, and are never reused. An entry created in the files
  without `uid` is new: the sync assigns `uid` and label, rewrites references
  to its placeholder, and writes both back.
- A sync compares entry by entry with the state stored at the last sync. An
  entry changed on one side only is carried to the other side. An entry
  changed on both sides, created on both sides with different content, or
  deleted on one side is a conflict and MUST NOT be overwritten or deleted;
  the owner decides per conflict (database, file, or defer). A manual sync
  MUST offer a preview; the direction MAY be restricted per run.
- An automatic sync (per project, default off) MUST carry only conflict-free
  changes, MUST NOT delete anything, MUST pause on unreadable files, merge
  markers, a running git operation, or a missing folder, and MUST back up the
  database before writing to it. Whether a project's sides differ MUST be
  detectable without changing any data.
- An owner MAY mark its mirror entries as ephemeral. For such entries a
  deletion in the database is carried to the files without a conflict, also
  by the automatic sync; a deletion in the files stays a conflict.
- Database: writes MUST be transactional and MUST abort with
  `version_conflict` instead of overwriting an element that changed since it
  was read. The schema is fixed: no free-form extra fields; fixed value lists
  are lookup tables. The schema MUST change only through forward-only,
  versioned migrations per owner, each preceded by a backup.
- Each plugin MUST own its tables (prefix `<plugin_id>_`). Foreign keys MAY
  point only to its own tables, the core's, or those of plugins in its
  `requires`. It reads other plugins' data only through their ports.
- Files: writes MUST be atomic (temporary file + rename), MUST keep line
  endings, and MUST abort with `mirror_conflict` instead of overwriting a file
  that changed since it was read. A codec MUST change only the affected
  entries and MUST reject values outside the format with file and line.
- The markdown format is "backlog format version 2", defined in
  `docs/techdocs/interfaces.md`. Byte-exact output is pinned by golden files
  in `tests/fixtures/mirror-v2/`.

### 3. Interfaces

- HTTP routes live under `/api/<owner>/…`, the MCP server under `/mcp`.
  Both MUST be generated from the same operations.
- Errors MUST be returned as `{code, message, details}` with a stable `code`,
  over HTTP and MCP alike; the frontend translates codes, not messages.
- Writing operations MUST take a version token.
- The TypeScript API types MUST be generated from the server's OpenAPI
  schema, never written by hand. Enforced by:
  `tests/implementation/integration/server/test_openapi_types.py`
  (created with `STORY-066`).
- The backend MUST reach the frontend only through Server-Sent Events on
  `/api/core/events`. Events are notifications; the frontend reloads data
  through the API. The frontend MUST NOT poll.
- There is no login. The server MUST listen on the local machine only.
- Permanently deleting data and changing settings MUST NOT be offered as MCP
  tools.

### 4. Time

- Points in time MUST be stored in UTC and shown and entered in the time zone
  of the machine the viewer runs on.
- Whether something is due MUST be decided by a pure function in `domain`
  that receives the current time as a parameter.
- Timers MUST go through the core's `Scheduler`: at most one pending point in
  time per owner, set to the next due point, no polling, active only while
  the server runs. The automatic sync is the only periodic timer; it runs
  only while at least one project has it switched on.
  Why: tests need a fixed clock, and an idle viewer must cost nothing.

### 5. Language

- Stored values (status, priority, type, field names in files) MUST be
  English; the UI translates them. Content is written in the project's
  language.

## Scopes

<!-- Areas with additional rules in architecture/<Scope>.md. A scope applies
in addition to this file, never instead of it. Paths: patterns relative to
the project root in backticks, comma-separated; `*` stays within one path
part, `**` spans any number of parts. Example row:
| llm-integration | `src/llm/**`, `src/prompts/*.py` | Model calls and prompts | -->

| Scope | Paths | Covers |
|---|---|---|
| server | `server/**` | Layers per core and plugin, ports, operations, errors, migrations, tests, dependencies |
| client | `client/**` | Layers, plugin contract, slots, state, domain logic, test ids, dependencies |
| legacy | `src_old/backend/**`, `src_old/web/**` | Storage, HTTP contract, and notes rules of the old viewer until the cutover |
| backend | `src_old/backend/**` | Old viewer: onion layers, dependency injection, error handling |
| web | `src_old/web/**` | Old viewer: React frontend structure, domain logic, state |

## Changing these rules

These rules are guidelines the project owner may deliberately break. If a
requirement or design does not fit them, the AI names the conflict and
proposes solutions, and the project owner decides (skill
`claude-harness:conflicts`). A change to this file or a scope file becomes
binding only after the project owner approves it.
