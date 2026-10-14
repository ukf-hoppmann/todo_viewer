# TASK-026 — Spec: Notes-Sync: Vorschau, Richtung, Konflikte und Label-Kollisionen

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-047), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Der Sync als Use Case in `application` auf zwei Ports, ohne Logik im Adapter (Architektur §1).

## Schon vorhanden
- Port `NotesMirror` und Adapter (TASK-025), Format (TASK-024), `NoteRepository`/`NoteDocumentStore`.
- Vorbild für Vorschau/Richtung/Konfliktabbruch: `application/services/sync.py`, `syncstatus.py`, `domain/sync.py`, API `POST /api/v2/sources/{source_id}/sync` und `GET /api/v2/sources/{source_id}/sync-status` in `api/v2/routers.py`.

## Festgelegtes Verhalten
- **Nie automatisch**, nie durch einen normalen Request. Nur ausdrücklicher Aufruf.
- Richtung: `to_mirror` (Standard: DB → Spiegel) oder `from_mirror` (Spiegel → DB).
- **Vorschau** (`dry_run`): listet je Note `neu`, `geändert`, `unverändert`, `nur im Ziel` (würde gelöscht) und Kollisionen; ändert nichts.
- **Löschen** im Ziel nur mit ausdrücklicher Bestätigung (`confirm_delete=true`), sonst bleiben „nur im Ziel“-Einträge unangetastet.
- **Konflikt** (Datei oder Note seit dem Lesen geändert) bricht den Lauf ab; nichts ist halb geschrieben.
- **Labels beim Import** (`from_mirror`): Eine Note mit Label, das in der Datenbank nicht existiert, bekommt ein **neues** Label des Projekts (der Zähler läuft weiter, Labels werden nie wiederverwendet); Verweise innerhalb der importierten Notes (`note:NOTE-007`) werden mit umgeschrieben. Existiert das Label schon mit anderem Inhalt, ist es eine Kollision: die Vorschau nennt sie, der Lauf verlangt je Kollision eine Entscheidung (`keep_db`, `take_mirror`, `import_as_new`).
- Links auf Items anderer Projekte bleiben Verweise `Projekt:Label` und werden nicht geprüft; Links, deren Ziel in der Zielumgebung fehlt, werden trotzdem übernommen und danach von der normalen Erreichbarkeitslogik (TASK-017) behandelt.
- Änderungs-Erkennung ohne Änderung: `notes_sync_status(source)` vergleicht den Fingerprint des Spiegels (TASK-025) und den Stand der Datenbank mit dem Stand des letzten Syncs (Fingerprints im `Source`-Sync-Zustand oder einer eigenen kleinen Tabelle; Entscheidung: **eigene Tabelle** `notes_sync_state` per Migration, damit der Backlog-Sync-Zustand unberührt bleibt).

## Zu tun
1. Domain `domain/notes_sync.py`: reine Funktionen für Diff, Kollisionserkennung, Label-Neuvergabe und Umschreiben der Verweise (alle ohne I/O).
2. `application/services/notes_sync.py`: `NotesSyncService.preview(source, direction)`, `run(source, direction, decisions, confirm_delete)`, `status(source)`.
3. Migration + Repository-Methoden für `notes_sync_state` (Contract-Test).
4. Routen: `GET /api/v2/sources/{source_id}/notes-sync-status`, `POST /api/v2/sources/{source_id}/notes-sync` Body `{direction, dry_run, decisions?, confirm_delete?}`.
5. OpenAPI neu erzeugen.

## Dateien
`domain/notes_sync.py` (neu), `application/services/notes_sync.py` (neu), `application/ports.py`, `application/container.py`, `bootstrap.py`, `infrastructure/database/schema.py`, `migrations.py`, `notes.py`, `api/v2/routers.py`, `schemas.py`, Tests `backend/tests/unit/domain/test_notes_sync.py`, `tests/integration/test_notes_sync.py` (Round-Trip mit Golden-Files), `tests/api_v2/test_notes_sync.py`.

## Nicht anfassen
Den Backlog-Sync (`sync.py`), den Datei-Adapter (TASK-025), die UI (TASK-027).

## Tests (zuerst)
Round-Trip DB → Spiegel → leere DB: alle Felder gleich (Text, Status, Topic-Pfad, Prüf-Datum, Modus, Auslöser inkl. `fired`/`already_met`, Links, Dokumente, Termine); Vorschau ändert nichts; Löschen nur mit Bestätigung; Konflikt bricht ab; Label-Neuvergabe und umgeschriebene Verweise; Kollision mit jeder der drei Entscheidungen; Status zeigt „Spiegel extern geändert“ nach Dateiänderung ohne Datenänderung.

## Stoppen und fragen
Wenn der Round-Trip eine Eigenschaft verliert, die TASK-024 nicht abbildet, oder wenn Label-Neuvergabe Links anderer Projekte auf die Note bricht (die zeigen auf das Original-Label).

## Abnahme
Round-Trip-Golden-Test, Vorschau-, Richtungs-, Konflikt- und Kollisionstests grün; `scripts/check.sh` grün.
