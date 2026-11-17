# Tests des Neubaus

Alle Tests (`server/`, `client/`) liegen hier.

```
implementation/unit/server/…         spiegelt server/src/viewer/, mit Fakes statt Adaptern
implementation/integration/server/…  echte SQLite-Datei, echte Ordner, echter uvicorn-Server, Contract-Suiten
implementation/system/server/…       ganzer Viewer, bedient über MCP wie vom Harness (STORY-081)
implementation/system/ops/…          Betrieb: `todo.sh`, Compose-Datei, Server als Prozess, Image (STORY-083)
implementation/unit/client/…         spiegelt client/src/ (Vitest, Testing Library)
fixtures/                            synthetische Testdaten (nie echte Backlogs)
helpers/server/                      Beispiel-Plugin und Hilfen nur für Tests
helpers/client/                      Fakes und Render-Hilfen für die Client-Tests
```

## Befehle

Einmalig: `python3.11 -m venv .venv && .venv/bin/pip install -e server`
bzw. die Abhängigkeiten aus `server/pyproject.toml`.

| Was | Befehl |
|---|---|
| Server: alle Tests | `cd server && ../.venv/bin/pytest` |
| Server: nur der Systemtest (MCP-Ablauf des Harness) | `cd server && ../.venv/bin/pytest -c pyproject.toml --rootdir=. ../tests/implementation/system` |
| Server: nur die Betriebs-Systemtests (ohne Image) | `cd server && ../.venv/bin/pytest -c pyproject.toml --rootdir=. ../tests/implementation/system/ops` |
| Image bauen, starten, `GET /api/core/health` (braucht Docker und `VIEWER_IMAGE_TEST=1`, sonst übersprungen) | `cd server && VIEWER_IMAGE_TEST=1 ../.venv/bin/pytest -c pyproject.toml --rootdir=. ../tests/implementation/system/ops/test_image.py` |
| Server: Lint, Typen, Schichtregeln, Tests | `scripts/check-next.sh` |
| Client: Installation | `cd client && npm ci` (verlinkt auch `tests/node_modules`, damit die Tests außerhalb von `client/` ihre Pakete finden) |
| Client: alle Tests | `cd client && npx vitest run --config configs/vite/vitest.config.ts` |
| Client: Typen, Lint (inkl. Architekturregeln) | `cd client && npx tsc -b && npm run lint` |
| Alter Viewer | `scripts/check.sh` |

Zeit ist in Tests immer eine feste Uhr; Tests von Anwendungsfällen laufen gegen
Fakes ihrer Ports.
