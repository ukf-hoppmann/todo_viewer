# `STORY-084` — Umstieg

Grundlage: `EPIC-007_spec.md`, Abschnitte 3, 11, 12.

## Umfang

- Vorher: Backup `configs/todo.db`, `configs/viewer.db` und der
  Spiegel-Ordner (Memory-Regel: geprüftes Backup vor Migration und
  Deployment).
- Übernahme (`STORY-082`) auf eine frische `configs/viewer.db`.
- Compose: Dienst `todo-viewer` zeigt auf das neue Image, Port 5411;
  `todo-viewer-next` entfällt; `todo.sh` ohne `next`.
- Erster Sync je Projekt Richtung Dateien (Format Version 2, `Uid`-Zeilen);
  der Inhaber committet die Spiegel in den betroffenen Repositories.
- Altcode entfernen, **erst nach ausdrücklicher Abnahme des Neubaus durch den
  Projektinhaber** (Regel 0): `src_old/`, `reference/`, alte Skripte, Scopes
  `legacy`, `backend`, `web`,
  alte `pyproject.toml`-Abschnitte.
- Ordner `configs/` aufräumen (Wunsch des Projektinhabers vom 2026-10-17: er
  weiß nicht, was wozu gehört). Vorher klären und im Ordner selbst in einer
  `configs/README.md` festhalten, was bleibt: `viewer.db` (und `-wal`/`-shm`,
  gehören zur laufenden Datenbank), `viewer.json`, `backups/` (mit Regel, wie
  lange was bleibt). Entfallen nach der Abnahme: `todo.db*` (alte Datenbank),
  `config.json`, `config.json.bak`, `ui_state.json.bak` (Reste der Übernahme
  aus früheren Versionen), die Projekt-Unterordner unter `backups/`. Nichts
  davon wird vor der Abnahme gelöscht.
- Doku: README, `docs/techdocs/*` auf den Neubau umschreiben.
- Übergabe an den Inhaber: Format Version 2 und MCP-Tool-Liste für die
  Anpassung des Harness (`[todo].api_url`, Helfer oder MCP).
- Version `1.0.0` (`STORY-060` Frage 11), Release nach Skill
  `claude-harness:semver`.

## Akzeptanz

Abschlusskriterien des Items; der Inhaber bestätigt den Betrieb.
