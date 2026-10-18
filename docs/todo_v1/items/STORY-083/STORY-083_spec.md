# `STORY-083` — Betrieb des Neubaus

Grundlage: `EPIC-007_spec.md`, Abschnitt 3.

## Umfang

- `server/Dockerfile` (mehrstufig: Node baut `client/`, Python-Image mit
  `server/`), Server liefert `client/dist` unter `/` aus, API unter
  `/api`, MCP unter `/mcp`.
- `docker-compose.yml`: neuer Dienst `todo-viewer-next`, Port 5412,
  `restart: unless-stopped`, Volumes `configs/`, `logs/`,
  Projekte-Ordner wie beim alten Dienst (`BROWSE_START`).
- `todo.sh next <befehl>`.
- Backups: Rotation aus `STORY-063`; dokumentieren.
- Doku: `docs/techdocs/operations.md`, Abschnitt Neubau.

## Tests

Systemtest (eigener Befehl): Image bauen, starten, `GET /api/core/health`.
