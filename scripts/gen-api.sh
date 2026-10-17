#!/bin/bash
# Erzeugt die TypeScript-Typen des Clients aus dem OpenAPI-Schema des Servers (Architektur §3).
# Aufruf: scripts/gen-api.sh  (oder `npm run gen:api` in client/)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON_BIN:-.venv/bin}
SCHEMA=client/.openapi.json

PYTHONPATH=server/src "$PY/python" -m viewer.app.openapi > "$SCHEMA"
mkdir -p client/src/shared/api
client/node_modules/.bin/openapi-typescript "$SCHEMA" -o client/src/shared/api/schema.d.ts
rm -f "$SCHEMA"
