# `STORY-082` — Datenübernahme

Grundlage: `EPIC-007_spec.md`, Abschnitte 7, 12.

## Umfang

- Befehl `viewer.app.import_legacy --legacy-db configs/todo.db --target
  configs/viewer.db [--dry-run]`; liest die alte DB nur lesend (SQLAlchemy,
  Schema aus `src_old/backend/todo_viewer/infrastructure/database/schema.py` als
  Vorlage), kein Import aus dem Altcode.
- Markdown-primäre Projekte: vorher mit dem alten Viewer in seine DB
  spiegeln, dann übernehmen (`STORY-060` Frage 1); der Befehl bricht ab, wenn ein
  Projekt noch Markdown-primär ist, und nennt es.
- Abbildungen:
  - Prioritäten wie in den Abschlusskriterien; leere Priorität → `Normal`.
  - Bereiche → `backlog_areas`.
  - `item_extra_fields` → datierter Notiz-Eintrag „Übernommene Zusatzfelder“
    (`STORY-060` Frage 4).
  - Zeit-Auslöser an Notes → Wecker mit Ziel Note (`STORY-060` Frage 7).
  - Links → `workspace_links` über `uid`.
  - Papierkorb- und Archivstand bleiben.
  - Label-Zähler = höchstes je vergebenes Label je Präfix (aus
    `note_counters` und den Labels).
- Spiegel-Einstellungen der Projekte übernehmen (Ordner, Auto-Sync,
  Richtung).
- Bericht als Text auf stdout und in `logs/import-<Zeit>.log`.

## Tests

Test zuerst mit einer synthetischen alten DB unter
`tests/fixtures/legacy-db/` (alle Fälle der Abbildungen); `--dry-run` ändert
nichts.
