# Betrieb

## Deployment

- Das `Dockerfile` baut in zwei Stages: zuerst das Frontend (`node:22-alpine`,
  `npm ci` + `npm run build`), dann das Backend-Image (`python:3.11-slim`), das
  API und `web/dist` ausliefert.
- `docker-compose.yml` startet den Dienst `todo-viewer` mit
  `restart: unless-stopped` auf Port 5411 und bindet ein:
  - `./configs` → `/app/configs` (Quellen und UI-Zustand bleiben auf dem Host),
  - `/Users/hoppmann/Documents/GitHub` unter demselben Pfad, beschreibbar
    (Bearbeitungen landen in den Backlog-Dateien der Nachbar-Repos).
- Aufruf im Browser: `http://todo.localhost:5411`.
- Nach Code-Änderungen: `./todo.sh update` (Neubau ohne Cache).
- CI: `.github/workflows/ci.yml` führt bei Push auf `main` und bei Pull
  Requests `scripts/check.sh` aus (ruff, mypy --strict, import-linter, pytest,
  tsc, eslint, vitest).

## Laufender Betrieb

- Starten/Stoppen über `./todo.sh` (siehe [README](../../README.md)).
- Status: `./todo.sh status`; Logs: `./todo.sh logs`.
- Es gibt keinen eigenen Health-Endpunkt; `GET /api/v2/backlog` antwortet auch
  ohne `config.json` (leerer Backlog).
- Das Frontend wird pro Anfrage gesucht: ein späteres `npm --prefix web run build`
  wird ohne Neustart ausgeliefert.

## Fehlerbilder

| Symptom | Ursache | Behebung |
|---|---|---|
| Seite zeigt „Frontend not built“ (HTTP 503) | `web/dist/index.html` fehlt (lokaler Start ohne Build) | `npm --prefix web run build` |
| Projekt in der Liste ausgegraut mit ⚠ | Backlog-Ordner fehlt, ist kein Ordner, enthält keine `TODO.md` oder ist im Container nicht eingebunden | Pfad in der UI (✎) oder in `config.json` korrigieren; Ordner muss unter dem gemounteten Pfad liegen |
| Speichern bricht mit Hinweis auf externe Änderung ab (`file_changed`/`entry_moved`) | Datei wurde zwischen Lesen und Schreiben geändert, z. B. durch einen Agenten | Nach dem nächsten Polling erneut bearbeiten |
| Speichern schlägt mit `write_failed` fehl | Keine Schreibrechte auf den Backlog-Ordner | Rechte bzw. Volume-Mount (beschreibbar) prüfen |
| Ein Test meldet veraltete API-Typen | v2-API geändert, `openapi.json`/`schema.d.ts` nicht neu erzeugt | `.venv/bin/python backend/scripts/export_openapi.py && npm --prefix web run gen:api` |
