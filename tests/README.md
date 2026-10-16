# Tests des Neubaus

Alle Tests des Neubaus (`server/`, `client/`) liegen hier. Die Tests des alten
Viewers liegen in `src_old/backend/tests/` und `src_old/web/` und laufen mit
`scripts/check.sh`.

```
implementation/unit/server/…         spiegelt server/src/viewer/, mit Fakes statt Adaptern
implementation/integration/server/…  echte SQLite-Datei, echte Ordner, echter uvicorn-Server, Contract-Suiten
implementation/unit/client/…         spiegelt client/src/ (Vitest, Testing Library)
fixtures/                            synthetische Testdaten (nie echte Backlogs)
helpers/server/                      Beispiel-Plugin und Hilfen nur für Tests
helpers/client/                      Fakes und Render-Hilfen für die Client-Tests
```

## Befehle

Einmalig: `python3.11 -m venv .venv && .venv/bin/pip install -r src_old/backend/requirements-dev.txt`
und `.venv/bin/pip install -e server` bzw. die Abhängigkeiten aus `server/pyproject.toml`.

| Was | Befehl |
|---|---|
| Server: alle Tests | `cd server && ../.venv/bin/pytest` |
| Server: Lint, Typen, Schichtregeln, Tests | `scripts/check-next.sh` |
| Client: Installation | `cd client && npm ci` (verlinkt auch `tests/node_modules`, damit die Tests außerhalb von `client/` ihre Pakete finden) |
| Client: alle Tests | `cd client && npx vitest run --config configs/vite/vitest.config.ts` |
| Client: Typen, Lint (inkl. Architekturregeln) | `cd client && npx tsc -b && npm run lint` |
| Alter Viewer | `scripts/check.sh` |

Zeit ist in Tests immer eine feste Uhr; Tests von Anwendungsfällen laufen gegen
Fakes ihrer Ports.
