# TASK-012 — Spec: Hinweise an Items, wenn eine verlinkte Note verworfen oder befördert wird

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-041), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Richtung Note → Item der STORY-041.

## Schon vorhanden (nach TASK-010)
Hinweis-Modell mit `side=item`, `NoticeCause.NOTE_DROPPED`/`NOTE_PROMOTED`, Entscheidung `acknowledge`, Routen `GET /api/v2/notices` und `POST /api/v2/notices/{id}/decision`.
- `NoteService.finish(project, label, version, target)` ist der einzige Weg in `dropped`/`promoted`; erledigt (`done`) erzeugt **keinen** Hinweis.

## Zu tun
1. In `NoteService.finish`: nach dem erfolgreichen Update bei `dropped` und `promoted` für jeden Link der Rolle `reference` mit Ziel-Art Item einen Hinweis `side=item` anlegen (Betroffener = das Item mit Projekt und Label, Gegenseite = die Note). Links der Rollen `trigger` und `origin` zählen nicht. Hinweis-Fehler brechen das Verwerfen nicht ab (wie TASK-011).
2. Entscheidung `acknowledge` (TASK-010) setzt den Hinweis auf erledigt; keine weitere Wirkung.
3. Item-Abfrage: `GET /api/v2/notices?side=item&project=<Projektname>&label=<ITEM-ID>&open=true` liefert die offenen Hinweise des Items (die Route aus TASK-010 deckt es ab; hier nur testen und ggf. den Filter ergänzen). Zusätzlich liefert `GET /api/v2/links-to` (TASK-007) pro Note ihren Status, damit die UI beides am Item zeigen kann.
4. Beförderung ruft `finish(…, promoted)`; STORY-042 muss hier nichts Eigenes tun, damit der Hinweis entsteht.
5. OpenAPI nur neu erzeugen, wenn sich Schemas ändern.

## Dateien
`application/services/notes.py`, ggf. `api/v2/notes_routers.py`/`schemas.py`, Tests `backend/tests/unit/application/test_note_notices.py` (Ergänzung aus TASK-011) und `tests/api_v2/test_notices.py`.

## Nicht anfassen
TASK-011 (Item → Note), die Fälligkeit der Note, Beförderungs-Abläufe.

## Tests (zuerst)
Verwerfen/Befördern mit einem Item-Link → ein Hinweis; mit zwei Items → zwei; `done` → keiner; `trigger`/`origin`-Link → keiner; Note ohne Links → keiner; Item in anderem Projekt; `acknowledge` schließt, zweites `acknowledge` abgelehnt; die Note wird durch Item-Hinweise **nicht** fällig.

## Stoppen und fragen
Wenn Item-Hinweise nach Projektname statt Quelle-ID adressiert werden müssen oder die Abfrage am Item eine andere Form braucht als in TASK-010 festgelegt.

## Abnahme
Beide Fälle per Test; `scripts/check.sh` grün.
