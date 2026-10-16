# Scope: legacy

Applies to `backend/**` and `web/**` in addition to `../architecture.md`
(whose sections apply to the new code only) and to the scopes `backend` and
`web`. These are the project-wide rules of the old viewer, unchanged. The
scope is removed at the cutover (`STORY-084`) together with the old code.

## 1. Storage backends behind ports

- This section governs the backlog (items and their documents). Notes
  (section 3) are not part of it.
- Each project MUST have exactly one primary source, chosen per project:
  markdown files or the central database. The primary source holds the truth:
  every request reads from and writes to it. A project MAY additionally keep a
  mirror in the other backend. A mirror MUST be written only by a sync, never
  by an ordinary request. The application MUST NOT keep any other copy of a
  project's data.
- All backends MUST implement the same storage ports and pass the same
  contract suite, as primary source and as mirror. Enforced by:
  `backend/tests/contract/`.
- The primary source MAY be switched per project. A switch MUST run a sync
  first so the new primary source is up to date, and MUST create a backup of
  the previous primary source; if either fails, nothing is switched.
- Markdown backend: writes MUST be atomic (temporary file + rename), MUST keep
  line endings, and MUST abort with a conflict error instead of overwriting a
  file that changed since it was read. Edits MUST change only the affected
  field or move the affected entry; byte-exact output is pinned by golden
  files. Enforced by: `backend/tests/characterization/test_edit.py`.
- Database backend: writes MUST be transactional and MUST abort with a
  conflict error instead of overwriting an item that changed since it was
  read. The schema MUST change only through versioned migrations.
- Data moves between backends only through a sync. A sync is requested by the
  user or an API call, or, only for a project whose owner switched auto-sync
  on (default: off), started by the application itself. Without the switch
  nothing moves automatically, not even after a write to the primary source.
  A manual sync MUST offer a preview and MUST NOT delete anything without an
  explicit decision.
- A sync compares entry by entry with the state stored at the last sync. An
  entry changed on one side only is carried to the other side. An entry
  changed on both sides, created on both sides with different content, or
  deleted on one side is a conflict and MUST NOT be overwritten or deleted;
  the owner decides per conflict (database, file, or defer). The direction
  MAY be restricted per run.
- An automatic sync MUST carry only conflict-free changes, MUST NOT delete
  anything, MUST NOT read unreadable files or files containing merge markers,
  and MUST create a backup before writing to the database.
- Whether a mirror differs from the primary source since the last sync MUST be
  detectable without changing any data, so the UI can show it.

## 2. One HTTP contract

- The frontend MUST talk to the backend only through API v2 (`/api/v2`).
- The TypeScript API types MUST be generated from the backend's OpenAPI
  schema, never written by hand. Enforced by:
  `backend/tests/api_v2/test_openapi.py`.
- Errors MUST be returned as `{code, message, details}` with a stable `code`;
  the frontend translates codes, not messages.

## 3. Notes, topics, and links

- Notes, topics, links, and triggers MUST live only in the central database,
  whatever the primary source of the project is. They MUST NOT be written to
  `TODO.md`, to any other markdown file, or to a mirror by an ordinary
  request; only the optional export (STORY-047) mirrors them as files.
  Why: markdown projects have no keys and no transactions across items, and
  notes must keep their links and triggers when a project switches backend.
  Enforced by: `pyproject.toml` (`[tool.importlinter]`, the markdown adapter
  does not import notes modules).
- Labels (`NOTE-001`, `TOPIC-001`) are counted per project and type, are never
  reused, and never change inside a project.
- Whether a trigger has arrived MUST be decided by a pure function in
  `domain` that receives the current time as a parameter. There MUST be no
  background timer for triggers: time triggers are evaluated when notes are
  read, event triggers in the use case that changes an item's status. The
  optional auto-sync of section 1 is exempt; it runs only while at least one
  project has its switch on.
  Why: tests need a fixed clock, and an idle viewer must cost nothing.
- Points in time MUST be stored unambiguously (UTC) and shown and entered in
  the time zone of the machine the viewer runs on.
