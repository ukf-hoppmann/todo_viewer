# STORY-059 — Auto-Sync für Projekte mit Spiegel (abschaltbar)

## 2026-10-14 — Architekturregel freigegeben und eingetragen (2026-10-14)

### Decided

- Der Besitzer hat den Wortlaut für docs/development/architecture.md §1 (Sync nur auf Anforderung oder bei eingeschaltetem Auto-Sync, Abgleich pro Eintrag, Auto-Sync nur Konfliktfreies/nie löschen/Backup) und §3 (Ausnahme vom Timer-Verbot für den Auto-Sync) freigegeben; die Änderung steht in der Datei und ist verbindlich.
- Offen bleibt die Umsetzung; sie folgt nach STORY-057.

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.
- Sichtprüfung: Die Projektkarten zeigen den Schalter „Automatisch abgleichen (nur Konfliktfreies, löscht nie)“, bei allen Projekten aus; die Sidebar markiert Projekte mit offenen Konflikten mit ⚠.

### Decided

- Intervall über die Umgebungsvariable `AUTO_SYNC_INTERVAL` (Sekunden, Standard 30, `0` = kein Timer), nicht in der Oberfläche. Beruhigung über das Token der Vorschau; der erste Lauf nach dem Start prüft nur, übernommen wird bei der zweiten Prüfung.
- Der Timer ist ein Daemon-Thread, der mit der App und beim Einschalten des Schalters startet und endet, sobald kein Projekt den Schalter hat. Auto-Läufe lesen streng: fehlender Ordner, unlesbare Dateien und Merge-Marker pausieren das Projekt (Merge-Marker: Start- und Endzeile). Letzter Lauf und Pause liegen nur im Speicher.
- Backup-Grund `auto`, höchstens einmal pro Stunde; Aufbewahrung die letzten 10 plus das jüngste je Tag der letzten 14 Tage. Migration 9 (`projects.auto_sync`), Fehler `auto_sync_needs_mirror` (400).
- Die Oberfläche fragt den Status jede Minute ab, solange ein Projekt den Schalter an hat, und lädt die Items bei einem neuen Lauf neu (Besitzer).

### Open

- Probelauf mit echtem `git pull` und Merge-Marker-Fall steht aus (nur Tests mit fester Uhr).
- Laufzeit der Prüfung bei großen Backlogs nicht gemessen; Verhalten des Timer-Threads beim Herunterfahren im Docker-Betrieb (`stop()` wartet höchstens 5 s) nicht geprüft.
