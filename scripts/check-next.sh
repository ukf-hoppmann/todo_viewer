#!/bin/bash
# Prüfungen des Neubaus (server/): Lint, Typen, Schichtregeln, Tests.
# Der alte Viewer wird weiter von scripts/check.sh geprüft.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=$(pwd)/${PYTHON_BIN:-.venv/bin}

cd server
"$PY/ruff" check src ../tests/implementation ../tests/helpers/server
TYPED=(src)
for d in ../tests/implementation/unit/server ../tests/implementation/integration/server ../tests/helpers/server; do
  [ -n "$(find "$d" -name '*.py' 2>/dev/null | head -1)" ] && TYPED+=("$d")
done
"$PY/mypy" "${TYPED[@]}"
(cd src && "$PY/lint-imports" --config ../pyproject.toml)
"$PY/pytest"
