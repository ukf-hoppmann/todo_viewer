# STORY-029 — Primärquelle und Spiegel pro Projekt in Modell und API

## 2026-09-30 — Umsetzung und Entscheidungen

### Discussed

- Die Datenbank-Kopie eines Markdown-Projekts gab es schon (gleiche project_id); es fehlte das Modell, nicht der Speicher.
- Neue Spalte mirror_database (Migration v3); path und sync_path bleiben, die API bekommt primary, markdown_path und mirror dazu.

### Decided

- Alte API-Felder bleiben, neue kommen dazu.
- Beim Wechsel der Primärquelle bleibt die bisherige Seite als Spiegel.
- Den Datenbank-Spiegel abschalten löscht die Kopie in der Datenbank, nie Markdown-Dateien.
- Release v0.6.1 (kompatible Erweiterung).

### Open

- Backup vor dem Wechsel (STORY-031) und Sync-Status (STORY-032) fehlen noch; der sync_required-Schutz beim Wechsel bleibt.
- Der laufende Container hat noch den alten Stand (./todo.sh update nötig).
