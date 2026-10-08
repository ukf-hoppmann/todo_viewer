# Scope: backend

Applies to `backend/**` in addition to `../architecture.md`.

## 1. Onion layers

- Dependencies MUST point inwards only: `bootstrap` → `api` | `infrastructure`
  → `application` → `domain`. `api` and `infrastructure` MUST NOT import each
  other. Enforced by: `pyproject.toml` (`[tool.importlinter]`, run by
  `scripts/check.sh`).
- `domain` and `application` MUST NOT use FastAPI, Pydantic, Starlette, or
  uvicorn. Enforced by: `pyproject.toml` (`[tool.importlinter]`).
- `domain` SHOULD use the standard library only.

## 2. Ports and composition

- `application` MUST define what it needs from the outside as ports
  (`typing.Protocol` in `application/ports.py`); adapters in `infrastructure`
  implement them.
- Adapters and services MUST be wired by constructor injection in
  `todo_viewer/bootstrap.py` only. No DI framework, no global singletons, no
  service locators outside the `Container`.
- Business rules (status transitions, archive moves, editable fields) MUST
  live in `domain`, not in parsers, adapters, or routers.

## 3. Errors

- Expected failures MUST be raised as subclasses of `DomainError` with a
  stable `code`. They MUST become HTTP responses only in `api/errors.py`.
- Routers MUST NOT build error responses themselves.

## 4. Tests

- Test data MUST be synthetic (`backend/tests/fixtures`), never copies of real
  backlogs.
- Services SHOULD be tested against in-memory fakes of their ports.

## 5. Storage adapters

- Adapters live in `infrastructure/markdown/` and `infrastructure/database/`
  and MUST NOT import each other. Enforced by: `pyproject.toml`
  (`[tool.importlinter]`).
- `domain` and `application` MUST NOT use SQLAlchemy or any database driver.
  Enforced by: `pyproject.toml` (`[tool.importlinter]`).
- The storage adapter MUST be chosen only by a routing adapter wired in
  `bootstrap.py`; services MUST NOT call different adapters depending on
  `Source.backend`. Domain code MAY use `Source.backend` to describe the
  project model (primary source, mirror, folders of each side).
- Sync between backends MUST be a use case in `application` working on two
  ports, not logic inside an adapter.
- The database's internal keys (`uid`) MUST NOT appear in `domain`,
  `application`, or the API; items are addressed by their label (`Item.id`),
  notes and topics by project plus label.
- Migrations MUST be forward-only and covered by a test that upgrades an empty
  database to the current version.

## 6. Notes and topics

- Notes, topics, links, and triggers MUST be reached through their own ports
  `NoteRepository` and `NoteDocumentStore` in `application/ports.py`, separate
  from `BacklogRepository`. There is one implementation in
  `infrastructure/database/`; it needs no routing adapter. It MUST pass the
  contract suite `backend/tests/contract/test_note_repository.py`.
- A link to a backlog item MUST store the project and the item's label, not a
  `uid`: markdown projects have no `uid`. The retype use case MUST update the
  links to the item in the same operation.
  Why: this keeps section 5 intact and works for both backends.
- The notes adapter MUST contain no trigger logic; the markdown adapter MUST NOT
  import notes modules. Enforced by: `pyproject.toml` (`[tool.importlinter]`).
- Access to another project's items (for links and event triggers) MUST go
  through the existing source lookup and `BacklogRepository`, never through
  an adapter import.
- Moving a note to another project MUST create it there with a new label and
  delete the old one (to the trash); the label of a note never changes.
- The topic depth limit (`notes.max_topic_depth`, default 3) is a business rule
  and MUST live in `domain`.
