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
