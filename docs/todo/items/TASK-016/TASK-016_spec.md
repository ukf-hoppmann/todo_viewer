# TASK-016 — Spec: Projektübergreifende Links und Ereignis-Auslöser prüfen und absichern

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-044), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Beweisen und absichern, was das Datenmodell schon kann. Es soll wenig Code entstehen; die Hauptarbeit ist der Test.

## Schon vorhanden
- Links speichern **Projektname plus Item-Label** (`LinkTarget(kind, project, label)`), nie eine `uid`.
- `NoteService.item_status_changed(project, item_id, status)` sucht Auslöser über `links_to` in **allen** Projekten; `ItemService` ruft es nach jedem Statuswechsel.
- `GET /api/v2/links-to` (TASK-007) gibt Notes aus allen Projekten zurück.
- Wirkung bei Markdown-Primärquelle: Ereignisse werden nur erkannt, wenn die Änderung über den Viewer läuft; eine Änderung außerhalb wird beim Sync erkannt (`application/services/sync.py`, STORY-040/023).

## Zu tun
1. Link-Ziel validieren: das Projekt muss registriert sein (`SourceRepository`), sonst Fehler `link_project_unknown`; das Item muss existieren (`link_target_not_found`, aus TASK-007). Gilt für `add_link` **und** `add_trigger`/`_checked_event`.
2. Anzeige: `LinkOut` (TASK-007) bekommt `target_display` = `"<Projekt> · <Label>"`; `NoteOut.triggers[].target` ebenso. Reine Funktion in `domain/` für die Formatierung (testbar).
3. **Prüfen** (nicht blind ändern), ob der Sync (Spiegel → Primärquelle, `sync.py`) bei geänderten Item-Status den Listener ruft. Wenn nicht: den kleinsten Weg ergänzen, dass ein Statuswechsel, den der Sync einspielt, `item_status_changed` auslöst; dabei keine Änderung des Sync-Verhaltens sonst. Ist der Aufwand größer als eine kleine Ergänzung, **anhalten und fragen** (dann eigene Task).
4. Integrationstest mit zwei Datenbank-Projekten und mit einem Markdown-Projekt als Ziel.

## Dateien
`application/services/notes.py`, `domain/notes.py` (Anzeigeformat), `api/v2/schemas.py`, `application/services/sync.py` (nur falls Punkt 3 es verlangt), Tests `backend/tests/integration/test_notes_flow.py` (neuer Fall), `tests/api_v2/test_note_links.py`.

## Nicht anfassen
Erreichbarkeit/`unreachable` (TASK-017), Hinweise (TASK-011), das Datenmodell.

## Tests (zuerst)
A→B: Merker in A, Auslöser auf Item in B (Zielstatus Completed); Item in B abschließen → Note in A fällig (Grund `trigger`); Zielstatus bereits erreicht → `already_met`; Rückrichtung `links-to` für das Item in B nennt die Note aus A; unbekanntes Projekt → `link_project_unknown`; Item-Label existiert nicht → `link_target_not_found`; Zielprojekt mit Markdown-Primärquelle.

## Stoppen und fragen
Wenn der Sync-Weg (3) mehr als eine kleine Ergänzung braucht, oder wenn die Validierung bestehende Notes mit Links auf entfernte Projekte unbenutzbar macht (das gehört zu TASK-017).

## Abnahme
Der Zwei-Projekte-Test belegt Auslösung und Rückrichtung; `scripts/check.sh` grün.
