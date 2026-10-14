# TASK-006 — Spec: Notes-API: Lebenszyklus, Auslöser, Archiv und Papierkorb

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-039), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Die Zustands- und Auslöser-Logik aus STORY-040 und STORY-043 (nur Service/Domain) per HTTP erreichbar machen.

## Schon vorhanden
- `NoteService.finish(project, label, version, target)` (done/dropped/promoted → Archiv), `snooze(project, label, version, review_at, trigger)`, `add_trigger(project, label, NewTrigger)`, `delete_note`, `restore_note`, `purge_note` (nur Besitzer), `trash(project)`.
- `NoteRepository.remove_trigger(project, label, trigger_id)` existiert, aber **kein** Service-Aufruf dafür.
- Übergangsregeln in `domain/note_lifecycle.py` (wirft `NoteLifecycleError`).

## Zu tun
1. `NoteService.remove_trigger(project, label, trigger_id)` ergänzen (der Port entfernt den Trigger samt seinem Link der Rolle `trigger`).
2. Schemas: `TriggerIn` (`kind`: time|event|topic_due, `at?`, `target?` = `{project, label}` des Items, `target_status?`), `TriggerOut` (wie `Trigger`, mit `fired_at`, `already_met`), `FinishIn` (`version`, `status`: **nur** `done` oder `dropped`), `SnoozeIn` (`version`, `review_at?`, `trigger?`), `TrashOut`.
3. Routen (`tags=["notes"]`):
   - `POST /api/v2/notes/{project}/{label}/finish` → `NoteOut`. `promoted` wird **abgelehnt** (Fehlercode `status_not_allowed`): befördert wird nur über STORY-042.
   - `POST /api/v2/notes/{project}/{label}/snooze` → `NoteOut`.
   - `POST /api/v2/notes/{project}/{label}/triggers` Body `TriggerIn` → 201 `TriggerOut`. Ereignis-Auslöser auf ein Item, dessen Ziel schon erreicht ist, feuert sofort (`already_met`), das liefert der Service schon.
   - `DELETE /api/v2/notes/{project}/{label}/triggers/{trigger_id}`.
   - `DELETE /api/v2/notes/{project}/{label}` → Note im Papierkorb (`NoteOut`).
   - `POST /api/v2/notes/{project}/{label}/restore` → `NoteOut` (aus Archiv oder Papierkorb, wird wartend).
   - `GET /api/v2/notes/{project}/trash` → `TrashOut` (Topics und Notes im Papierkorb). Diese Route steht **vor** `/{project}/{label}` im Router.
   - **Keine** Purge-Route für Notes oder Topics.
4. Zeitpunkte: ISO mit Zeitzone; ohne Zeitzone gilt die lokale Zeit des Rechners (`domain.notes.utc`). „Morgen früh“ löst der Aufrufer auf.
5. OpenAPI neu erzeugen.

## Dateien
`application/services/notes.py`, `api/v2/notes_routers.py`, `api/v2/schemas.py`, generierte Web-API-Dateien, Tests `backend/tests/api_v2/test_notes_lifecycle.py` (neu).

## Nicht anfassen
Beförderung (STORY-042), Änderungshinweise (STORY-041), die Logik in `domain/notes.py` und `note_lifecycle.py`.

## Tests (zuerst)
Je Route Erfolg und Fehler: `finish` mit `promoted` abgelehnt; `finish` einer bereits archivierten Note abgelehnt; `snooze` setzt gefeuerte Auslöser zurück und akzeptiert neues Datum/neuen Auslöser; Zeit-Auslöser in der Vergangenheit feuert beim Lesen (fester `Clock` aus `tests/conftest.py`/Fakes); Ereignis-Auslöser auf bereits erreichtes Item → `already_met`; Auslöser entfernen entfernt auch den Link; Löschen, Papierkorb-Liste, Wiederherstellen; es gibt keine DELETE-Route auf `/trash/...`, die endgültig löscht.

## Stoppen und fragen
Wenn die Übergänge in `note_lifecycle.py` anders sind als die Fehlerfälle oben, oder wenn ein Auslöser auf ein Item in einem Projekt ohne Quelle andere Fehler liefert als `SourceGoneError`.

## Abnahme
Alle Operationen und abgelehnten Übergänge per API-Test; kein Weg zum endgültigen Löschen; `scripts/check.sh` grün.
