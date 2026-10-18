# TASK-004 — Spec: Topics-API: anlegen, lesen, ändern, verschieben, löschen

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-039), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Die Topic-Operationen des vorhandenen `NoteService` sind über `/api/v2` erreichbar. Diese Task legt außerdem den Rahmen an, den TASK-005 bis TASK-009 nutzen.

## Schon vorhanden (nicht neu bauen)
- `application/services/notes.py` (`NoteService`): `delete_topic(project, label, cascade)`, `restore_topic`, `purge_topic` (nur Besitzer, **keine Route**), `trash(project)`.
- `NoteRepository` (`application/ports.py`): `create_topic`, `get_topic`, `list_topics`, `update_topic`, `move_topic`; Tiefe und Schleifen prüft `domain/notes.py` (`check_new_topic`, `check_topic_move`) und wirft `TopicTooDeepError` / `TopicLoopError` / `TopicNotFoundError`.
- `NotesSettings.max_topic_depth` (Standard 3) kommt aus `infrastructure/config/notes.py`.
- Noch **keine** Notes-Route und kein Notes-Schema in `api/v2/`.

## Zu tun
1. `NoteService` bekommt die fehlenden Topic-Methoden: `create_topic`, `show_topic`, `list_topics`, `rename_topic_or_set_due` (Name und `due_at` ändern), `move_topic`. Sie rufen nur den Port und reichen `settings.max_topic_depth` durch. Keine Geschäftsregel im Router.
2. Neue Schemas in `api/v2/schemas.py` (`TopicOut`, `TopicCreate`, `TopicPatch`, `TopicMove`, `TopicTrashOut`).
3. Neue Routen in `api/v2/routers.py` mit `tags=["topics"]`, **Projekt = Projektname** (`Source.project`), nie `uid`:
   - `POST /api/v2/topics` Body `{project, name, parent?, due_at?}` → 201 `TopicOut`.
   - `GET /api/v2/topics/{project}/{label}` → `TopicOut`.
   - `PATCH /api/v2/topics/{project}/{label}` Body `{name?, due_at?}`; `due_at: null` entfernt den Termin (Muster wie das PATCH der Items, mit `model_fields_set` unterscheiden).
   - `POST /api/v2/topics/{project}/{label}/move` Body `{parent: string|null}`.
   - `DELETE /api/v2/topics/{project}/{label}?cascade=false` → Papierkorb-Inhalt; ohne `cascade` bei einem Topic mit Notes oder Unter-Topics Fehler (so wie `plan_topic_delete` es vorgibt).
   - `POST /api/v2/topics/{project}/{label}/restore` → Papierkorb-Inhalt.
   - **Kein** Purge-Endpunkt.
4. `TopicOut`: `project`, `label`, `name`, `parent`, `due_at`, `path` (Liste der Namen von der Wurzel), `depth`, `deleted`. Zeitpunkte als ISO-Zeitstempel mit Zeitzone (UTC).
5. Fehlerabbildung: die vorhandenen Domain-Fehler (`TopicNotFoundError` 404, `TopicTooDeepError`/`TopicLoopError` 400, `NoteLifecycleError` 409) laufen über `api/errors.py`. Neue Codes nur, wenn nötig; sie stehen in der Fehlerliste unten in den Backlog-Notes dieser Task (Eingangsmaterial für STORY-046).
6. `application/container.py` / `bootstrap.py`: `NoteService` ist schon verdrahtet (`bootstrap.py` um Zeile 110); prüfen, dass `Container.notes` im Router ankommt, sonst ergänzen.
7. OpenAPI neu erzeugen (`python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`).

## Schnittstellen, die später gelten (hier festlegen, TASK-005 bis TASK-009 und die UI übernehmen sie)
- Router-Datei: Notes-Routen in einer eigenen Datei `api/v2/notes_routers.py`, in `api/v2/__init__.py` eingebunden, damit `routers.py` nicht weiter wächst.
- Pfad-Muster: Ressourcen unter `/api/v2/topics` und `/api/v2/notes`, immer `{project}/{label}`.
- Versionstoken: Notes tragen `version` (siehe `Note.version`); Topics haben keinen Versionstoken (nur Name/Termin, last write wins) — das hier so lassen.

## Dateien
`api/v2/notes_routers.py` (neu), `api/v2/schemas.py`, `api/v2/__init__.py`, `application/services/notes.py`, `application/container.py`, `bootstrap.py`, `web/src/api/openapi.json` + `schema.d.ts` (nur generiert), Tests unter `backend/tests/api_v2/test_topics.py` (neu), ggf. `backend/tests/unit/application/test_note_service.py`.

## Nicht anfassen
Note-Routen (TASK-005 bis TASK-009), Datenmodell/Migrationen, `domain/note_lifecycle.py`, das Backlog-Routing, `purge_*`.

## Tests (zuerst schreiben, müssen aus dem erwarteten Grund fehlschlagen)
API-Test mit der Fixture `api`/`workspace` wie in `tests/api_v2/test_v2.py`: anlegen (mit/ohne Parent), Tiefe 4 abgelehnt, unbekannter Parent 404, verschieben mit Schleife abgelehnt, Termin setzen und mit `null` entfernen, löschen ohne Kaskade bei vorhandenen Notes abgelehnt, mit Kaskade ok, Wiederherstellen, unbekanntes Projekt.

## Stoppen und fragen
Wenn die Fehlerabbildung eines vorhandenen Domain-Fehlers nicht zu den Codes passt, wenn `Container.notes` anders heißt oder wenn `test_openapi.py` nach dem Neuerzeugen nicht grün wird.

## Abnahme
Alle Operationen per API-Test; keine `uid` in Antworten; `scripts/check.sh` grün.
