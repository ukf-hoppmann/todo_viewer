# TASK-007 — Spec: Links-API: setzen, lösen, in beide Richtungen abfragen

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-039), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Der `NoteService` bekommt die Link-Operationen, die HTTP-Routen kommen darauf.

## Schon vorhanden
- `NoteRepository.add_link(project, label, LinkTarget, LinkRole)`, `remove_link`, `links_of(project, label)`, `links_to(LinkTarget)` (über alle Projekte), `relink_item`.
- `LinkTarget(kind, project, label)`, `LinkRole`: `reference`, `trigger`, `origin`.
- Item-Ziele werden über die Quelle des Projekts und `BacklogRepository.get` geprüft (siehe `NoteService._checked_event` als Muster).

## Zu tun
1. Service: `add_link`, `remove_link`, `links_of`, `links_to`.
   - Rolle `reference` darf der Aufrufer setzen. `trigger` entsteht nur über einen Ereignis-Auslöser (TASK-006), `origin` nur durch Beförderung/Rückstufung (STORY-042): beide über diese Route → Fehler `link_role_not_allowed`.
   - Ziel prüfen: Item (Projekt registriert und Item vorhanden, auch Archiv), Topic und Note (im angegebenen Projekt vorhanden). Sonst `link_target_not_found` (404-artiger Fehler, neuer `NotFoundError` in `domain/errors.py`).
   - Doppelter Link gleicher Rolle auf dasselbe Ziel → idempotent (kein zweiter Eintrag).
   - Ein Link darf nicht auf die Note selbst zeigen.
2. **Vorab prüfen:** `application/services/retype.py` ruft `relink_item(source.id, …)`, alle Links speichern aber den **Projektnamen** (`Source.project`, siehe `items.py` `item_status_changed(source.project, …)` und `NoteService._source`). Per Test mit einem Link auf ein Item und anschließendem `retype` beweisen, dass der Link dem Item folgt. Ist es ein Fehler (Link bleibt am alten Label), im selben Zug beheben (`source.project` statt `source.id`) und den Test behalten.
3. Schemas: `LinkIn` (`target`: `{kind, project, label}`, `role` Standard `reference`), `LinkOut` (`id`, `note` = `{project, label}`, `target`, `role`, plus für Item-Ziele `target_title`, `target_status` falls lesbar, sonst `null`).
4. Routen (`tags=["links"]`):
   - `POST /api/v2/notes/{project}/{label}/links` → 201 `LinkOut`.
   - `DELETE /api/v2/notes/{project}/{label}/links/{link_id}`; Links der Rolle `trigger` lassen sich so nicht lösen (Fehler `link_role_not_allowed`, sie gehen mit dem Auslöser).
   - `GET /api/v2/notes/{project}/{label}/links` → Links der Note.
   - `GET /api/v2/links-to?kind=item&project=…&label=…` → die Notes (kompakt: Projekt, Label, Kurzfassung, Status, Rolle), die auf dieses Ziel zeigen, projektübergreifend. Das ist „Notes zu Item X“.
5. OpenAPI neu erzeugen.

## Dateien
`application/services/notes.py`, `application/services/retype.py` (nur falls der Fehler aus 2 bestätigt wird), `domain/errors.py`, `api/errors.py` (nur falls ein neuer Fehlertyp eine Abbildung braucht), `api/v2/notes_routers.py`, `api/v2/schemas.py`, Tests `backend/tests/api_v2/test_note_links.py` (neu), `tests/integration/test_notes_flow.py` (Retype-Fall, falls dort sinnvoll).

## Nicht anfassen
Projektübergreifende Erreichbarkeit (STORY-044), Hinweise (STORY-041), die Link-Tabelle selbst.

## Tests (zuerst)
Link auf Item/Topic/Note setzen; unbekanntes Ziel; Rolle `trigger`/`origin` abgelehnt; doppelt setzen ändert nichts; lösen; Rückrichtung findet die Note; Link überlebt `retype` (Test schlägt vorher ggf. fehl → Bug aus 2).

## Stoppen und fragen
Wenn `links_to` nicht nach Projekt und Label eines **archivierten** Items findet, oder wenn der `retype`-Fehler weitere Aufrufstellen betrifft.

## Abnahme
Setzen, lösen, beide Abfragen per API-Test; Retype-Test grün; `scripts/check.sh` grün.
