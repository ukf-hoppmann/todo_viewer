# TASK-032 — Stand je Eintrag speichern und Änderungsseite erkennen

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.
- Migration 8 lief an einer Kopie der echten Datenbank (alle 14 alten Tabellen inhaltsgleich) und danach auf der echten Datenbank (Zeilenzahlen wie im Backup).

### Decided

- Die Tabelle `sync_entries` hat zusätzlich die Schlüsselspalte `folder`: ohne sie wäre der Stand nach einem Wechsel des Sync-Ordners falsch und ein Konflikt könnte still überschrieben werden. Kein Fremdschlüssel auf `projects`.
- Klassifikation je Eintrag: unverändert, Datenbank oder Markdown geändert, beide geändert, auf einer Seite neu, beide neu (verschieden), auf einer Seite gelöscht. Konflikte: beide geändert, beide neu, einseitig gelöscht.
- Der Stand wird am Ende des Laufs aus einem erneuten Lesen beider Seiten geschrieben (nur wo beide gleich sind), nicht aus der Absicht; ein Abbruch hinterlässt so keinen falschen Stand.
- Die Vorschau hat keine Felder `missing`/`missing_documents` mehr, dafür `origin` und `conflicts`. Der Sync-Status meldet bei offenen Konflikten `state: conflicts` (Besitzer).

### Open

- Laufzeit bei sehr vielen Einträgen nicht gemessen (der Stand wird für jede Statusabfrage geladen).
