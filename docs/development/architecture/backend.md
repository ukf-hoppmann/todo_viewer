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
  `application`, or the API; items are addressed by their label (`Item.id`).
- Migrations MUST be forward-only and covered by a test that upgrades an empty
  database to the current version.
