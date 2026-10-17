#!/bin/bash
# Prüfungen des Neubaus (server/): Lint, Typen, Schichtregeln, Tests.
# Der alte Viewer wird weiter von scripts/check.sh geprüft.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=$(pwd)/${PYTHON_BIN:-.venv/bin}

cd server
"$PY/ruff" check src ../tests/implementation ../tests/helpers/server
TYPED=(src)
for d in ../tests/implementation/unit/server ../tests/implementation/integration/server ../tests/implementation/system/server ../tests/helpers/server; do
  [ -n "$(find "$d" -name '*.py' 2>/dev/null | head -1)" ] && TYPED+=("$d")
done
"$PY/mypy" "${TYPED[@]}"
(cd src && "$PY/lint-imports" --config ../pyproject.toml)
"$PY/pytest"

# Client: Typen, Architekturregeln und Lint, Tests
cd ../client
[ -d node_modules ] || npm ci --no-audit --no-fund
node configs/linkTestModules.mjs
npx tsc -b
npm run lint --silent
npx vitest run --config configs/vite/vitest.config.ts
