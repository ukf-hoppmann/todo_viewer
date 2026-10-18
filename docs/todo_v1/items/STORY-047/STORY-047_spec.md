# STORY-047 — Spec: Notes als Markdown exportieren, importieren, abgleichen

## Was und warum
Notes leben in API und Datenbank. Die Markdown-Spiegelung ist eine Option, damit Claude Notes auch dort nutzen kann, wo der Viewer nicht erreichbar ist (Cloud, claude.ai), und damit Rechner über Git abgleichen können. Es ist kein Normalbetrieb. Neufassung nach den Entscheidungen des Besitzers vom 2026-10-14.

## Regeln (architecture.md §1 und §3)
- Der Abgleich ist ein ausdrücklicher Sync, nie automatisch und nie durch einen normalen Request. Er bietet eine Vorschau, löscht nichts ohne Bestätigung, lässt die Richtung wählen. Dateien werden atomar geschrieben und brechen mit Konflikt ab, wenn sie sich seit dem Lesen geändert haben.
- **Ein Sync für alles:** Notes laufen im selben Sync wie der Backlog (`POST /sources/{id}/sync`): eine Vorschau, ein Token, ein Status, ein Konflikt-Dialog. Der Use Case arbeitet auf Ports (`NotesMirror` für die Dateiseite, `NoteRepository` und `NoteDocumentStore` für die Datenbank), ohne Logik im Adapter.
- Der Abgleich pro Eintrag (STORY-057) gilt auch für Topics, Notes und Note-Dokumente; Konflikte entscheidet der Besitzer im Dialog aus STORY-058 (Datenbank, Datei oder aufschieben).
- Notes liegen immer in der Datenbank (Architektur §3), auch bei Projekten mit Markdown als Primärquelle; für Notes ist die Dateiseite immer der Spiegel.
- Der Datei-Adapter liegt in `infrastructure/notes_files/`, nicht in `infrastructure/markdown/` (der Import-Linter verbietet dem Markdown-Adapter Notes-Module).

## Was gespiegelt wird
Topics (Baum, Termin, Created, Deleted), Notes (Summary, Status, Prüf-Datum, Modus, Created, Updated, Archived, Deleted, Langtext), Links, Auslöser (inkl. `fired_at` und `already_met`), Note-Dokumente (Notizen, Specs) und die Label-Zähler. Nicht gespiegelt: Änderungshinweise (`note_notices`), Projektliste, UI-Zustand, Notes-Einstellungen (`max_topic_depth`, `review_days`; sie gelten je Rechner).
Papierkorb und Archiv: Die Datei bleibt in `notes/`, markiert durch `Deleted` bzw. `Archived`. Eine endgültig gelöschte Note hat keine Datei mehr; fehlt eine Datei, die im gespeicherten Stand vorkommt, meldet die Vorschau sie als „fehlt“, gelöscht wird nur mit Bestätigung.

## Notes ohne Label (Cloud)
In den Dateien neu angelegte Notes heißen `new-<kurzname>.md` und tragen kein Label (erste Zeile `# NEW`). Der Import vergibt das nächste freie Label des Projekts aus dem Zähler und schreibt Verweise darauf um; der nächste Export benennt die Datei in `NOTE-xxx.md` um. Dasselbe gilt für Topics. Dadurch vergibt nur die Datenbank Labels, und unabhängig angelegte Notes kollidieren nicht.

## Import darf nicht an Regeln scheitern
Links auf Projekte oder Labels, die es nicht gibt, bleiben erhalten (die Erreichbarkeitslogik behandelt sie). Topic-Bäume tiefer als `max_topic_depth` werden eingelesen. Unbekannte Kopfzeilen, ungültige Status und kaputte Zeitpunkte sind dagegen Formatfehler mit Zeilennummer, kein stilles Überspringen.

## Format
Festgelegt in TASK-024 (Dateien in `notes/`: `NOTE-xxx.md`, Dokumente daneben, `topics.md`, `counters.md`). Das Format wird in `docs/techdocs/interfaces.md` beschrieben, damit der Harness (Dateimodus) dagegen bauen kann; eine Zeile je Auslöser und Link, damit Git sauber zusammenführt.

## Reihenfolge
Zuerst STORY-057 (Abgleich pro Eintrag, inkl. Backup) und STORY-058 (Konflikt-Dialog); danach TASK-024 → TASK-025 → TASK-026 → TASK-027.

## Datenbank-Backup
Vorgabe des Besitzers: Vor jedem Schritt, der die echte Datenbank oder ihr Schema berührt, liegt ein frisches Backup in `configs/backups/` (ab TASK-031 automatisch).

## Betroffene Dateien
`domain/notes_markdown.py`, `domain/notes_sync.py`, `domain/sync.py`, `application/services/sync.py`, `syncstatus.py`, `application/ports.py`, neues Paket `infrastructure/notes_files/`, `pyproject.toml` (Import-Linter), `api/v2/*`, `web/src/components/SyncDialog.tsx`, `docs/techdocs/interfaces.md`.

## Abnahme
- Round-Trip ohne Verlust von Text, Notizen, Specs, Links, Auslösern, Terminen, Topic-Baum, Archiv-/Papierkorbstand und Zählern (Golden-File-Test über die ganze Kette).
- Eine Note ohne Label aus den Dateien erhält beim Import ein Label.
- Der Sync hat Vorschau, Richtungswahl, Konfliktentscheidung wie der Backlog-Sync.
