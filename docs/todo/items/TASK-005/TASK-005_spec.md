# TASK-005 — Spec: Notes-API: anlegen, lesen, ändern, Projekt wechseln

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-039), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Die Kernoperationen für Notes über `/api/v2`. Lebenszyklus, Auslöser, Links, Dokumente und Index folgen in TASK-006 bis TASK-009.

## Schon vorhanden
- `NoteService.create`, `edit` (nur Kurzfassung und Langtext; ein geänderter Text setzt `review_at` neu), `keep`, `show`.
- `NoteRepository.update_note(project, label, expected_version, NoteChanges)` wirft `VersionConflictError` bei altem Token; `NoteChanges` kennt `topic`/`clear_topic`, `trigger_mode`.
- `NoteRepository.move_note(project, label, target_project, target_topic, at)`: legt die Note im Zielprojekt mit **neuem Label** an (Links, Auslöser, Dokumente kommen mit, Links anderer Notes folgen) und löscht die alte in den Papierkorb. Die Regeln dazu stehen in `docs/development/architecture.md` und `backend.md` §6.
- `NoteView` (Note + Triggers + `NoteEvaluation`) ist die Antwortform des Service.
- Routen-Rahmen und Schemas aus TASK-004 (`api/v2/notes_routers.py`).

## Zu tun
1. `NoteService.edit` erweitern: zusätzlich `topic` (Label oder `None` = entfernen) und `trigger_mode`. Das Topic muss im selben Projekt existieren (`TopicNotFoundError`). Das Prüf-Datum wird nur bei geändertem Text neu gesetzt (wie bisher).
2. Neue Service-Methode `move_to_project(project, label, version, target_project, target_topic)`: prüft die Version (`VersionConflictError`), prüft, dass das Zielprojekt registriert ist (`SourceGoneError`), ruft `move_note` und gibt die **neue** Note zurück. Hinweise an verlinkte Items (STORY-041) gehören nicht hierher.
3. Schemas: `NoteOut` (`project`, `label`, `summary`, `body`, `status` = effektiver Zustand, `stored_status`, `reason`, `topic`, `topic_path`, `review_at`, `trigger_mode`, `archived`, `deleted`, `version`, `triggers[]`, `fired[]`, `all_fired`, `created`, `updated`), `NoteCreate`, `NotePatch`, `NoteMove`.
4. Routen (`tags=["notes"]`):
   - `POST /api/v2/notes` Body `{project, summary, body?, topic?, review_at?, trigger_mode?}` → 201 `NoteOut`. `summary` ist Pflicht und eine Zeile (mehrzeilig → `bad_request`/`invalid_value`).
   - `GET /api/v2/notes/{project}/{label}` → `NoteOut` (auch aus Archiv und Papierkorb lesbar, `archived`/`deleted` zeigen es).
   - `PATCH /api/v2/notes/{project}/{label}` Body `{version, summary?, body?, topic?, trigger_mode?}`; `body: null` und `topic: null` leeren das Feld.
   - `POST /api/v2/notes/{project}/{label}/keep` Body `{version}`.
   - `POST /api/v2/notes/{project}/{label}/move` Body `{version, target_project, target_topic?}` → `NoteOut` der neuen Note.
5. OpenAPI neu erzeugen.

## Dateien
`application/services/notes.py`, `api/v2/notes_routers.py`, `api/v2/schemas.py`, `web/src/api/*` (generiert), Tests `backend/tests/api_v2/test_notes.py` (neu) und `tests/unit/application/test_note_service.py` (Ergänzungen).

## Nicht anfassen
`infrastructure/database/notes.py` (Port ist fertig, Contract-Suite bleibt), Lebenszyklus-Routen (TASK-006), Hinweise (STORY-041).

## Tests (zuerst)
Anlegen/Lesen/Ändern; zweimal mit demselben Token ändern → 409 `version_conflict`; Text ändern setzt `review_at` neu, Topic-Wechsel nicht; unbekanntes Topic 404; Projektwechsel: neue Note hat neues Label im Zielprojekt, alte liegt im Papierkorb, Antwort nennt das neue Label; Zielprojekt unbekannt; `keep` setzt nur `review_at`.

## Stoppen und fragen
Wenn `move_note` Links oder Auslöser anders behandelt als hier beschrieben, oder wenn ein Topic des Zielprojekts angegeben werden muss, das `move_note` nicht kennt.

## Abnahme
Alle Operationen per API-Test inklusive Versionskonflikt; `scripts/check.sh` grün.
