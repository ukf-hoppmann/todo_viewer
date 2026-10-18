# STORY-047 — Notes in Markdown spiegeln und zwischen Rechnern abgleichen

## 2026-10-08 — Vorbereitung der Umsetzung

### Discussed

- Rolle von Markdown für Notes
- Nutzung in der Cloud

### Decided

- Story ist Pflicht (Besitzer-Entscheidung); Markdown ist nur Export, Import und Sync, nicht der Normalbetrieb.
- Notes werden samt Notizen und Specs gespiegelt; Links werden als Label-Verweise geschrieben.

### Open

- Dateiformat und Ordnerstruktur sind ein Vorschlag und werden vor der Umsetzung bestätigt.
- Verhalten bei Label-Kollisionen beim Import.

## 2026-10-14 — Neufassung nach Abstimmung (Notes im gemeinsamen Sync)

### Discussed

- Ziel: Backlog und Notes in der Cloud (claude.ai) nutzen, per Git zwischen Rechnern abgleichen und lokal in der Datenbank bearbeiten.
- Was fehlt für „alles“: Notes-Sync, Abgleich pro Eintrag, Konflikt-Dialog, Backup.

### Decided

- Ein Sync für Backlog und Notes (eine Vorschau, ein Token, ein Status) statt eines eigenen Notes-Syncs; TASK-026 und TASK-027 entsprechend angepasst.
- Neue Voraussetzungen: STORY-057 (Abgleich pro Eintrag, Backup) und STORY-058 (Konflikt-Dialog); STORY-047 hängt davon ab.
- Notes ohne Label aus der Cloud (new-<kurzname>.md); die Datenbank vergibt das Label beim Import.
- Papierkorb- und Archivstand, fired_at, already_met, Created/Updated und die Label-Zähler wandern mit; Änderungshinweise nicht.
- Dateiformat: ein Eintrag je Zeile (Auslöser, Links), Topic als Label; Datei-Adapter im neuen Paket infrastructure/notes_files/ (Import-Linter).
- Vor Schritten an der echten Datenbank ein Backup (Vorgabe des Besitzers); Stand 2026-10-14 15:27 liegt unter configs/backups/.

### Open

- Richtung im Abgleich pro Eintrag (siehe STORY-057).
- Die Fingerabdrücke von Source.baseline umfassen künftig Backlog und Notes; bestehende Baselines gelten einmalig als geändert (im Plan von TASK-026 prüfen).

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.
- Round-Trip Datenbank → Dateien → leere Datenbank an einer Kopie der echten Datenbank für `ToDo_viewer` und `ezf-ui` ohne Abweichung (siehe TASK-026).

### Decided

- Notes laufen im selben Sync wie der Backlog (eine Vorschau, ein Status, ein Konflikt-Dialog). Neu in der Cloud angelegte Notes haben kein Label (`new-<kurzname>.md`), die Datenbank vergibt es beim Import. Papierkorb- und Archivstand, `fired_at`, `already_met`, `Created`/`Updated` und die Zähler wandern mit, Änderungshinweise (`note_notices`) nicht.
- Der Datei-Adapter liegt in `infrastructure/notes_files/`, nicht in `infrastructure/markdown/` (Import-Linter). Der Auto-Sync importiert Notes ohne Label und benennt die Dateien um (Besitzer).

### Open

- Der Harness (Dateimodus) wurde noch nicht gegen das Format in `docs/techdocs/interfaces.md` geprüft.
- Ein echter Cloud-Lauf (claude.ai) mit Git steht aus.
