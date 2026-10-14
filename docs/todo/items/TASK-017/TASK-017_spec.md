# TASK-017 — Spec: Nicht erreichbare Projekte: Link markieren und Hinweis erzeugen

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-044), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Erreichbarkeit als **berechnete** Eigenschaft von Links, plus ein Hinweis (TASK-010) beim ersten Entdecken.

## Schon vorhanden
- Hinweis-Modell mit Ursache `project_unreachable` (TASK-010), Entscheidungen, Fälligkeit mit Grund `notice`.
- `NoteService._source(project)` wirft `SourceGoneError`, wenn das Projekt nicht (mehr) registriert ist; Backlog-Lesen kann an `OSError`/Quellenfehlern scheitern.
- Kein Hintergrund-Takt (Architekturregel): Auswertung nur beim Lesen.

## Festgelegtes Verhalten
- Ein Link auf ein Item ist `unreachable`, wenn das Projekt nicht registriert ist **oder** seine Quelle nicht gelesen werden kann (`SourceGoneError` oder `OSError`/Lesefehler aus `BacklogRepository.get`). Ein Item, das es im erreichbaren Projekt nicht gibt, ist **nicht** `unreachable` (das ist `link_target_not_found`/Löschen, TASK-011).
- `reachable` wird nicht gespeichert, sondern bei Bedarf berechnet. Gespeichert wird nur der Hinweis.
- Ausgewertet wird, wenn eine Note gelesen wird (`NoteService.show`), ihre Links gelesen werden (`links_of`) und beim Aufbau der Fällig-Liste (`due_all`). Nicht im Index und nicht im Zähler (zu teuer; der Zähler zählt vorhandene Hinweise).
- Beim ersten Entdecken wird ein Hinweis `project_unreachable` angelegt, wenn für diesen Link keiner offen ist (TASK-010 vermeidet Doppelte). Kommt das Projekt zurück, wird nichts gelöscht und nichts entschieden.
- Kein Fehler: jeder Lesefehler wird abgefangen und als `reachable=false` gemeldet; die Fehlerursache steht kurz in `unreachable_reason` (kein Pfad, keine Geheimnisse).

## Zu tun
1. Reine Funktion in `domain/` (z. B. `reachability_of(project_registered: bool, read_ok: bool)`), und eine Service-Methode `link_reachability(link)` in `NoteService`, die `SourceRepository`/`BacklogRepository` nutzt (Zugriff auf andere Projekte nur darüber, nie über Adapter).
2. `LinkOut` (TASK-007) und die Trigger-Ziele in `NoteOut` bekommen `reachable` (bool) und `unreachable_reason` (string|null).
3. In `show`, `links_of` und `due_all` den Hinweis anlegen (nur wenn kein offener gleicher Hinweis existiert).
4. OpenAPI neu erzeugen.

## Dateien
`domain/notes.py` (oder `domain/notices.py`), `application/services/notes.py`, `api/v2/schemas.py`, Tests `backend/tests/unit/application/test_note_reachability.py` (neu), `tests/api_v2/test_note_links.py`, `tests/integration/test_notes_flow.py`.

## Nicht anfassen
Index/Zähler, Entscheidungs-Logik (TASK-010), Sync, das Registrieren von Projekten.

## Tests (zuerst)
Projekt entfernt → `reachable=false`, ein Hinweis, kein Fehler; zweites Lesen → kein zweiter Hinweis; Quelle wirft `OSError` → gleiche Behandlung; Projekt kehrt zurück → `reachable=true`, Hinweis bleibt offen; Item fehlt in erreichbarem Projekt → nicht `unreachable`; lokale Links (eigenes Projekt) werden nie als unreachable gemeldet, wenn das Projekt lesbar ist.

## Stoppen und fragen
Wenn ein Lesefehler des Markdown-Backends sich nicht von „Item existiert nicht“ unterscheiden lässt, oder wenn `due_all` durch die Auswertung spürbar langsam wird (dann Messwert nennen).

## Abnahme
Beide Fälle per Test, kein Fehler an den Aufrufer; `scripts/check.sh` grün.
