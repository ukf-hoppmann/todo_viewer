# Architecture rules

<!-- Binding architecture of this project. Always English; MUST, SHOULD, and
MAY have their RFC 2119 meaning. Keep this file short: rules that apply to the
whole project only. Rules for one area go into a scope file. A rule that can
be checked mechanically names its test, e.g. "Enforced by:
tests/architecture/test_layers.py". -->

## Rules

### 1. Backlog files are the source of truth

- The application MUST NOT keep its own copy of backlog data. Items are read
  from and written to the configured markdown files on every request.
- Writes to backlog files MUST be atomic (temporary file + rename), MUST keep
  line endings, and MUST abort with a conflict error instead of overwriting a
  file that changed since it was read.
- Edits MUST change only the affected field or move the affected entry;
  byte-exact output is pinned by golden files. Enforced by:
  `backend/tests/characterization/test_edit.py`.

### 2. One HTTP contract

- The frontend MUST talk to the backend only through API v2 (`/api/v2`).
- The TypeScript API types MUST be generated from the backend's OpenAPI
  schema, never written by hand. Enforced by:
  `backend/tests/api_v2/test_openapi.py`.
- Errors MUST be returned as `{code, message, details}` with a stable `code`;
  the frontend translates codes, not messages.

## Scopes

<!-- Areas with additional rules in architecture/<Scope>.md. A scope applies
in addition to this file, never instead of it. Paths: patterns relative to
the project root in backticks, comma-separated; `*` stays within one path
part, `**` spans any number of parts. Example row:
| llm-integration | `src/llm/**`, `src/prompts/*.py` | Model calls and prompts | -->

| Scope | Paths | Covers |
|---|---|---|
| backend | `backend/**` | Onion layers, dependency injection, error handling |
| web | `web/**` | React frontend structure, domain logic, state |

## Changing these rules

These rules are guidelines the project owner may deliberately break. If a
requirement or design does not fit them, the AI names the conflict and
proposes solutions, and the project owner decides (skill
`claude-harness:conflicts`). A change to this file or a scope file becomes
binding only after the project owner approves it.
