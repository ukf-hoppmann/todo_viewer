#!/bin/bash
# Alle Backend-Prüfungen: Lint, Typen, Schichtregeln, Tests.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON_BIN:-.venv/bin}

"$PY/ruff" check src_old/backend
"$PY/mypy" --strict src_old/backend/todo_viewer
(cd src_old/backend && "../../$PY/lint-imports" --config ../../pyproject.toml)
"$PY/pytest"

# Frontend: Typen, Lint, Tests
(cd src_old/web && npx tsc -b && npx eslint . && npx vitest run)
