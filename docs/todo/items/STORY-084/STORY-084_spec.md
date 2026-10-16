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
- Altcode entfernen: `backend/`, `web/`, alte Skripte, Scope `legacy`,
  alte `pyproject.toml`-Abschnitte.
- Doku: README, `docs/techdocs/*` auf den Neubau umschreiben.
- Übergabe an den Inhaber: Format Version 2 und MCP-Tool-Liste für die
  Anpassung des Harness (`[todo].api_url`, Helfer oder MCP).
- Altitems nach `STORY-060` Frage 3.
- Version `1.0.0` (`STORY-060` Frage 11), Release nach Skill
  `claude-harness:semver`.

## Akzeptanz

Abschlusskriterien des Items; der Inhaber bestätigt den Betrieb.
