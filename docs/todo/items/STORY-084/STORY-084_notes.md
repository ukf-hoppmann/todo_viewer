# STORY-084 — Umstieg: der Neubau ersetzt den alten Viewer

## 2026-10-16 — Entscheidungen

### Decided

- Harter Schnitt beim Umstieg, kein Parallelbetrieb.
- Das Markdown-Format wird hier definiert; der Harness wird danach vom Projektinhaber angepasst.

## 2026-10-17 — Ordner configs aufräumen

### Discussed

- Der Projektinhaber weiß nicht, welche Dateien in configs/ wozu gehören: config.json (leer, Rest der alten Projektliste), config.json.bak und ui_state.json.bak (Sicherungen aus der ersten Übernahme), todo.db mit -wal und -shm (die alte Datenbank samt SQLite-Begleitdateien), backups/ (Datenbank-Sicherungen und je Projekt Sicherungen von Markdown-Ordnern).

### Decided

- Beim Umstieg wird configs/ aufgeräumt und mit einer README beschrieben; gelöscht wird erst nach der Abnahme des Neubaus.
