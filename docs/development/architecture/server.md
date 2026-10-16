# Scope: server

Applies to `server/**` in addition to `../architecture.md`.

## 1. Layers

- The core (`viewer/core/`) and every plugin (`viewer/plugins/<id>/`) MUST
  be split into `domain`, `application`, `infrastructure`, and `api`.
  Dependencies MUST point inwards only: `api` | `infrastructure` →
  `application` → `domain`. `api` and `infrastructure` MUST NOT import each
  other. Enforced by: `server/pyproject.toml` (`[tool.importlinter]`).
- `domain` and `application` MUST NOT use FastAPI, Pydantic, Starlette,
  uvicorn, SQLAlchemy, or the MCP SDK. Enforced by: `server/pyproject.toml`
  (`[tool.importlinter]`).
- `domain` SHOULD use the standard library only. Parsing and rendering of a
  markdown format are pure functions in `domain`; reading and writing the
  files belongs to the codec adapter in `infrastructure`.
- A plugin's `plugin.py` MAY import every layer of its own plugin; it holds
  only the plugin definition.

## 2. Ports and composition

- `application` MUST define what it needs from outside as ports
  (`typing.Protocol`) in `application/ports.py` of its owner; adapters in
  `infrastructure` implement them. Ports of another plugin are used only if
  that plugin is in `requires`.
- Every plugin MUST export exactly one `PluginDefinition` from `plugin.py`.
  Importing it MUST have no side effects; the plugin builds its services
  only in `build(context)`.
- Adapters and services MUST be wired by constructor injection, only in
  `viewer/app/composition.py` and the `build` functions it calls. No DI
  framework, no global singletons, no service locators.
- Business rules (status transitions, parent rules, due decisions, label
  rules) MUST live in `domain`, not in codecs, adapters, or the hosts.

## 3. Operations

- An operation's input and output MUST be dataclasses (or lists of them);
  its handler is a use case in `application`. JSON schemas are derived only
  in the core's HTTP and MCP hosts.
- Operation names are `snake_case` and unique per owner; the MCP tool is
  `<owner>_<name>`.

## 4. Errors

- Expected failures MUST be raised as subclasses of `DomainError` with a
  stable `code`. They MUST become HTTP or MCP errors only in the core's
  hosts. Plugins MUST NOT build error responses.

## 5. Storage

- Database access MUST stay in `infrastructure/database/` of its owner and
  go through the core's engine and transaction port. File access MUST go
  through the core's `FileStore` port; plugins MUST NOT touch the file system
  directly.
- Every owner's migrations MUST be covered by a test that upgrades an empty
  database to the current version.
- Every `FileStore` adapter and every plugin's codec and sync participant
  MUST pass a contract suite under
  `tests/implementation/integration/server/contract/`.

## 6. Tests

- Tests live under `tests/implementation/unit/server/` (mirroring
  `server/src/viewer/`) and `tests/implementation/integration/server/`.
- Test data MUST be synthetic (`tests/fixtures/`), never copies of real
  backlogs or notes.
- Use cases SHOULD be tested against in-memory fakes of their ports; time
  only with a fixed clock.

## 7. Dependencies

- A new runtime dependency in `server/pyproject.toml` MUST be approved by
  the project owner before it is added. Approved with this scope: FastAPI,
  uvicorn, SQLAlchemy, Pydantic, the official MCP SDK (`mcp`), structlog.
