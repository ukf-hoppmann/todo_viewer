#!/bin/bash
# Alle Backend-Prüfungen: Lint, Typen, Schichtregeln, Tests.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON_BIN:-.venv/bin}

"$PY/ruff" check backend
"$PY/mypy" --strict backend/todo_viewer
(cd backend && "../$PY/lint-imports" --config ../pyproject.toml)
"$PY/pytest"
