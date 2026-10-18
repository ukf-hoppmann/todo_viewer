# TASK-009 — Spec: Notes-Index, Fällig-Zähler, Fällig-Liste und Notes-Einstellungen

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-039), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Die Lese-Sichten, die Tokens sparen und das rote Ausrufezeichen speisen.

## Schon vorhanden
- `NoteService.overview(project, archived)`, `due(project)`, `trash(project)`; `NoteView` mit `evaluation` (`status`, `reason`, `fired`, `all_fired`).
- Zeit-Auslöser werden beim Lesen ausgewertet (Clock-Port), kein Hintergrund-Takt.
- `NotesSettings` wird in `bootstrap.py` (um Zeile 110) einmal aus `configs/config.json` gelesen und fest an `NoteService` übergeben (`infrastructure/config/notes.py`). Das muss ohne Neustart änderbar werden.
- `links_to` aus TASK-007 für den Filter „verlinktes Item“.

## Zu tun
1. Service-Methoden (reine Lesewege, kein Schreiben):
   - `index(project=None, topic=None, status=None, due=None, linked_project=None, linked_item=None, archived=False)` liefert Topic-Zeilen (`project`, `label`, `name`, `path`, `due_at`) und Note-Zeilen (`project`, `label`, `summary`, `status` effektiv, `reason`, `due_at` = Zeitpunkt der Fälligkeit mit Grund, `topic`, `review_at`). **Nie** `body`, Auslöser oder Dokumente. Projekt leer = alle Projekte. `topic` filtert auch den Teilbaum.
   - `due_all()` projektübergreifend, nur Notes im Zustand fällig, mit `reason` und `fired` (Auslöser-Ids) sowie `actions`: Liste der möglichen Aktionen (`snooze`, `done`, `drop`, `promote`; spätere Hinweise ergänzen `keep`, `detach`). Die Zuordnung Grund → Aktionen ist eine reine Funktion in `domain/` (testbar).
   - `due_count()` = Länge von `due_all()`; Platz für spätere Hinweise (STORY-041) bleibt: die Zählung läuft über eine Funktion, die TASK-010 erweitern kann.
2. Einstellungen: `NotesSettings`-Quelle als Provider (`Callable[[], NotesSettings]`) statt fester Instanz an `NoteService`; neuer Service/Port zum Lesen und Schreiben der beiden Werte in `configs/config.json` (Muster `infrastructure/config/json_file.py`, `ui_state.py`, atomar schreiben). Werte validieren: `max_topic_depth` 1 bis 10, `review_days` 1 bis 3650 (`InvalidValueError`). Ein geändertes `max_topic_depth` verändert vorhandene Topics nicht, es gilt für neue und verschobene.
3. Routen (`tags=["notes"]`), die festen Pfade **vor** den `{project}/{label}`-Routen:
   - `GET /api/v2/notes-index?project&topic&status&due&linked_project&linked_item&archived` → `{topics[], notes[]}`.
   - `GET /api/v2/notes-due/count` → `{count}`. Eigener, billiger Aufruf, liest keine Langtexte.
   - `GET /api/v2/notes-due` → Fällig-Liste.
   - `GET /api/v2/notes-settings` → `{max_topic_depth, review_days}`; `PUT /api/v2/notes-settings` Body mit denselben Feldern.
4. OpenAPI neu erzeugen.

## Dateien
`application/services/notes.py`, `domain/notes.py` (nur Aktionen-Zuordnung, oder neue `domain/note_views.py`), `application/ports.py` (Settings-Port), `infrastructure/config/notes.py`, `bootstrap.py`, `api/v2/notes_routers.py`, `api/v2/schemas.py`, Tests `backend/tests/api_v2/test_notes_index.py` (neu), `tests/unit/domain/` für die Aktionen-Zuordnung.

## Nicht anfassen
Hinweise (STORY-041), UI, die Logik von `evaluate`.

## Tests (zuerst)
Index enthält nie `body`; je Filter ein Fall (Projekt, Topic mit Teilbaum, Status, fällig, verlinktes Item, Archiv); Zähler steigt, wenn ein Zeit-Auslöser mit festem Clock erreicht ist, und sinkt nach Zurückstellen/Erledigen; Fällig-Liste über zwei Projekte; Einstellungen schreiben/lesen, ungültige Werte abgelehnt, neuer Wert gilt für den nächsten Request.

## Stoppen und fragen
Wenn die Einstellungen in `configs/config.json` an einer anderen Stelle liegen als `notes.max_topic_depth` / `notes.review_days`, oder wenn der Provider-Umbau weitere Aufrufer von `NotesSettings` betrifft.

## Abnahme
Index, Zähler, Fällig-Liste und Einstellungen per API-Test; `scripts/check.sh` grün.
