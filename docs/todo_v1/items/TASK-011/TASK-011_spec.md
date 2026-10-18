# TASK-011 — Spec: Hinweise an Notes bei Änderung eines verlinkten Items

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-041), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Richtung Item → Note der STORY-041.

## Schon vorhanden (nach TASK-010)
`add_notice`, `NoticeCause` (`item_completed`, `item_rejected`, `item_deleted`, `item_retyped`), `links_to(LinkTarget)` über alle Projekte.
- Statuswechsel: `ItemService` ruft in `application/services/items.py` (um Zeile 88) `ItemStatusListener.item_status_changed(project, item_id, status)`; `NoteService` implementiert ihn für Auslöser.
- Löschen: `application/services/trash.py`. Typwechsel: `application/services/retype.py`, dort wird `relink_item` aufgerufen (der Link überlebt, die Note soll es erfahren).

## Zu tun
1. `ItemStatusListener` um zwei Ereignisse erweitern: `item_deleted(project, item_id)` und `item_retyped(project, old_id, new_id)`. Die Aufrufe kommen in `trash.py` (nach erfolgreichem Verschieben in den Papierkorb) und `retype.py` (nach erfolgreichem Umbenennen, **nach** `relink_item`, damit der Hinweis den neuen Label trägt). Fehlt der Listener (None), passiert nichts, wie heute.
2. `NoteService.item_status_changed` behält die Auslöser-Logik und ergänzt: bei `Completed` oder `Rejected` für jeden Link der Rolle **reference** auf das Item (aktive, nicht abgeschlossene, nicht gelöschte Note) einen Hinweis `item_completed`/`item_rejected` anlegen. Bei Rolle `trigger` entscheidet der Auslöser, kein Hinweis. Rolle `origin` nie.
3. `item_deleted` → Hinweis `item_deleted` an jede Note mit Link `reference`. `item_retyped` → Hinweis `item_retyped` mit der neuen ID als Gegenseite (der Link wurde schon umgehängt).
4. Wiederherstellen eines gelöschten Items erzeugt keinen Hinweis und löscht keinen vorhandenen.
5. Fehler im Hinweis-Pfad dürfen die Änderung am Item nicht verhindern: Hinweis-Anlage nach dem erfolgreichen Item-Schreiben, Fehler wird protokolliert (`request_log.note`/Logger wie im Projekt üblich), nicht an den Aufrufer geworfen.

## Dateien
`application/ports.py` (Listener), `application/services/items.py`, `trash.py`, `retype.py`, `notes.py`, Tests `backend/tests/unit/application/test_note_notices.py` (neu), `tests/integration/test_notes_flow.py` (ein Durchlauf mit zwei Projekten).

## Nicht anfassen
Hinweise in Gegenrichtung (TASK-012), Erreichbarkeit (TASK-017), die Entscheidungslogik aus TASK-010.

## Tests (zuerst; eine Zeile der Matrix je Test)
Ursache × Rolle: `reference` + {abgeschlossen, verworfen, gelöscht, retype} → je ein Hinweis; `trigger` → keiner; `origin` → keiner; archivierte oder gelöschte Note → keiner; Item in anderem Projekt als die Note; zweiter Statuswechsel zum selben Status erzeugt keinen zweiten offenen Hinweis; Item-Schreiben gelingt auch, wenn die Hinweis-Anlage fehlschlägt (Fake wirft).

## Stoppen und fragen
Wenn `trash.py` oder `retype.py` keine Stelle hat, an der der Listener nach Erfolg gerufen werden kann, oder die Reihenfolge von `relink_item` und Hinweis anders sein muss.

## Abnahme
Testmatrix grün; keine Note verschwindet still; `scripts/check.sh` grün.
