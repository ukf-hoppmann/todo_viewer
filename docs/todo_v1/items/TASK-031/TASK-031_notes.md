# TASK-031 — Automatisches Datenbank-Backup vor Migration und Sync

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.
- Beim ersten Start mit Schema 7 legte der Viewer selbst `todo-20261016-064129-migration.db` an; die Probe an einer Kopie der echten Datenbank lieferte dasselbe, Backup mit integrity_check ok.

### Decided

- Dateiname `todo-JJJJMMTT-HHMMSS-<migration|sync|auto>.db`, Wiederholung in derselben Sekunde `-2`, `-3`; Aufbewahrung die letzten 10 dieser Muster, andere Dateien im Ordner (auch von Hand angelegte) bleiben.
- Sicherung zuerst in eine `.partial`-Datei mit der SQLite-Backup-Funktion (`journal_mode=DELETE`, `integrity_check`, Zeilenzahl je Tabelle), erst danach Umbenennen.
- Backup vor Migration nur bei einem Schema 1 bis CURRENT−1 (nicht bei neuer oder aktueller Datenbank); vor Sync nur, wenn der Lauf in die Datenbank schreibt; nur SQLite.
- Fehlerfall: 409 `database_backup_failed` bei der ersten Anfrage (die Migration läuft träge beim ersten Zugriff), kein Abbruch beim Start. Am 2026-10-16 vom Besitzer mit „ja“ bestätigt.
