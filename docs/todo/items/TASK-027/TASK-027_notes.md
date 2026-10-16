# TASK-027 — Notes im gemeinsamen Sync-Dialog bedienen

## 2026-10-14 — Umbau auf den gemeinsamen Sync-Dialog

### Decided

- Kein eigener NotesSyncDialog und keine notes-sync-Hooks: Notes erscheinen im vorhandenen Sync-Dialog; Konflikte im Dialog aus STORY-058.
- Neue Abhängigkeit auf STORY-058.

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.
- Sichtprüfung am laufenden Viewer (nur Vorschau, nichts ausgeführt): Die Vorschau von `ToDo_viewer` zeigt neben Einträgen und Dokumenten einen eigenen Abschnitt NOTES (2 neu, Richtung Datenbank → Ordner).

### Decided

- Abschnitte für Topics, Notes und Notes-Dokumente erscheinen nur, wenn etwas drin ist. Note-Konflikte werden feldweise dargestellt, der Langtext als Zeilenvergleich; der Fehlertext für `note_format` nennt Datei und Zeile.

### Open

- Ein Notes-Konflikt ist in den echten Daten nicht vorhanden; seine Darstellung ist nur durch Komponententests belegt.
