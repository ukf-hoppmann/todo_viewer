# TASK-026 — Spec: Notes-Sync: Vorschau, Richtung, Konflikte und Label-Kollisionen

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-047), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- **Datenbank-Backup zuerst (Vorgabe des Besitzers):** Bevor ein Schritt die echte Datenbank oder ihr Schema berührt, liegt ein frisches Backup in `configs/backups/` (ab TASK-031 automatisch). Sync-Läufe und Migrationen zuerst an einer Kopie von `configs/todo.db` prüfen.
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Die Notes (Topics, Notes, Links, Auslöser, Note-Dokumente, Zähler) laufen im bestehenden Sync mit: derselbe Endpunkt (`POST /sources/{id}/sync`, `GET .../sync-status`), dieselbe Vorschau, dasselbe Token, dieselben Konfliktentscheidungen (STORY-057, TASK-033). Kein zweiter Endpunkt, keine zweite Zustandstabelle. Der Ablauf ist ein Use Case in `application` auf Ports, ohne Logik im Adapter (Architektur §1).

## Schon vorhanden / Abhängigkeiten
- TASK-024 (Format), TASK-025 (`NotesMirror` + Adapter), TASK-032 und TASK-033 (Stand je Eintrag, Konflikte, Entscheidungen), `NoteRepository` und `NoteDocumentStore`.
- Vorbild und Erweiterungspunkt: `application/services/sync.py`, `syncstatus.py`, `domain/sync.py`.
- Architektur §3: Notes liegen immer in der Datenbank; für Notes ist die Dateiseite immer der Spiegel, auch bei Projekten mit Markdown als Primärquelle.

## Festgelegtes Verhalten
- Neue Eintragsarten im Stand je Eintrag: `topic`, `note`, `note_document`. Klassifikation, Konflikte, Entscheidungen, Vorschau und „Löschen nur mit Bestätigung“ wie beim Backlog.
- **Labels beim Import** (Datei → Datenbank): Eine Note oder ein Topic ohne Label (`new-<kurzname>.md`, `NEW`) bekommt das nächste freie Label des Projekts. Verweise in den importierten Dateien (`note:new-<kurzname>`, `Topic: new:<Name>`) werden mit umgeschrieben; der nächste Export schreibt die Datei als `NOTE-xxx.md`. Zähler = Maximum aus Datenbank, Datei und höchstem vorkommenden Label; Labels werden nie wiederverwendet (Architektur §3).
- Labels vergibt nur die Datenbank, deshalb kollidieren unabhängig angelegte Notes nicht. Existiert ein Label auf beiden Seiten und wurde es auf beiden Seiten geändert, ist das ein normaler Konflikt.
- Links auf Items anderer Projekte oder auf unbekannte Ziele bleiben Verweise `Projekt:Label`, werden nicht geprüft und trotzdem übernommen (Erreichbarkeitslogik TASK-017).
- Topics tiefer als `max_topic_depth` werden eingelesen; die Grenze gilt für die Bedienung, nicht für den Import.
- Papierkorb und Archiv wandern mit (`Deleted`, `Archived`). Änderungshinweise (`note_notices`) werden nicht gespiegelt.
- Gesamtstatus (`state`, `conflicts`) und Fingerabdrücke (`Source.baseline`) umfassen Backlog und Notes. Dadurch gelten bestehende Baselines einmalig als geändert, bis zum nächsten Sync; im Plan prüfen und dem Besitzer sagen.
- Ein Sync, der Notes in die Datenbank schreibt, legt vorher ein Backup an (TASK-031).

## Zu tun
1. Domain `domain/notes_sync.py`: reine Funktionen für Label-Vergabe, Umschreiben der Verweise, Zählerableitung und den Vergleichsstand von Topics, Notes und Note-Dokumenten (ohne I/O).
2. `SyncService` und `SyncStatusService` auf die zusätzlichen Ports erweitern (`NotesMirror`, `NoteRepository`, `NoteDocumentStore`); Vorschau, Ausführen und Status decken Notes mit ab.
3. API-Schema: Vorschau-Abschnitte für Topics, Notes und Note-Dokumente; OpenAPI neu erzeugen.
4. Format und Verhalten in `docs/techdocs/interfaces.md` beschreiben (der Harness baut dagegen).

## Dateien
`domain/notes_sync.py` (neu), `domain/sync.py`, `application/services/sync.py`, `syncstatus.py`, `application/ports.py`, `application/container.py`, `bootstrap.py`, `infrastructure/database/notes.py`, `api/v2/routers.py`, `schemas.py`, Tests `backend/tests/unit/domain/test_notes_sync.py`, `tests/integration/test_notes_sync.py` (Round-Trip mit Golden-Files), `tests/api_v2/test_notes_sync.py`, Doku.

## Nicht anfassen
Den Datei-Adapter (TASK-025), die UI (TASK-027), die Mechanik des Stands je Eintrag (TASK-032).

## Tests (zuerst)
Round-Trip DB → Spiegel → leere DB: alle Felder gleich (Text, Status, Topic, Prüf-Datum, Modus, Auslöser inkl. `fired`/`already_met`, Links, Dokumente, Termine, Archiv-/Papierkorbstand, Zähler); Vorschau ändert nichts; Löschen nur mit Bestätigung; Note ohne Label bekommt ein Label, Verweise werden umgeschrieben, Zähler steigt nie rückwärts; Konflikt bei Änderung auf beiden Seiten mit jeder Entscheidung; Status zeigt „Spiegel extern geändert“ nach Dateiänderung ohne Datenänderung; Link auf unbekanntes Ziel bleibt erhalten.

## Stoppen und fragen
Wenn der Round-Trip eine Eigenschaft verliert, die TASK-024 nicht abbildet; wenn die Label-Vergabe Links anderer Projekte auf eine Note bricht (sie zeigen auf das Original-Label); wenn die Erweiterung der Fingerabdrücke mehr als den einmaligen Baseline-Wechsel auslöst.

## Abnahme
Round-Trip-Golden-Test, Vorschau-, Konflikt- und Labeltests grün; Status deckt Notes ab; `scripts/check.sh` grün.
