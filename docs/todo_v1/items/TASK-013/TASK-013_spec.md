# TASK-013 — Spec: Note zu Task, Story oder Epic befördern (Backend)

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-042), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Richtung Note → Item der STORY-042 (Backend und HTTP). Die UI folgt in TASK-015.

## Schon vorhanden
- `ItemService.create(source, item_type, fields)` (`application/services/items.py`) mit allen Backlog-Prüfungen; Fehler wie `parent_closed` kommen von dort.
- `DocumentService` (Items) und `NoteDocumentService` (TASK-008) für Notizen/Specs; `NoteService.finish(…, promoted)` archiviert; Link-Methoden aus TASK-007; Entscheidung `promote` ist in TASK-010 als `decision_not_available` vorbereitet.
- Zwei Speicher: das Projekt kann Markdown-Primärquelle haben, Notes liegen in der Datenbank. Es gibt keine gemeinsame Transaktion.

## Festgelegter Ablauf (Reihenfolge ist Pflicht)
1. Prüfen: Note existiert, ist weder archiviert noch gelöscht, Token passt.
2. Item anlegen über `ItemService.create`. Der Aufrufer liefert `item_type` (`Task`/`Story`/`Epic`), `area`, `goal`, `completion_criteria`, `parent?`, `required_for_parent?`, `priority?`, `dependencies?`; `title` und `summary` sind vorbelegt aus der Kurzfassung der Note, der Aufrufer darf sie überschreiben.
3. **Sofort danach** den Link `origin` Note → Item anlegen. Er ist der Beleg, dass Schritt 2 gelaufen ist.
4. Dokumente übernehmen: der Langtext der Note wird der **erste datierte Eintrag** der Notizen des Items (Thema „Aus Note <LABEL> befördert“, Abschnitt `Discussed`); die Dokumente der Note (`<LABEL>_notes.md`, `<LABEL>_spec.md`, `<LABEL>_spec_<topic>.md`) werden unverändert an die Notizen/Specs des Items angehängt oder dort angelegt (Namen mit der Item-ID).
5. `finish(…, promoted)` setzt die Note auf `promoted` und ins Archiv (löst nebenbei die Item-Hinweise aus TASK-012 aus).
6. Fehler nach Schritt 3: die Antwort nennt Zustand und Item; **wiederholen** ist idempotent: Existiert für die Note bereits ein `origin`-Link auf ein vorhandenes Item, wird Schritt 2 übersprungen, die Schritte 4 und 5 laufen für das Fehlende weiter (Dokumente nur kopieren, wenn sie am Item noch nicht stehen; den Langtext-Eintrag nur, wenn er noch fehlt).

## Zu tun
1. Neuer Service `application/services/conversion.py` (`ConversionService.promote(...)`), nicht in `NoteService`. Domain-Regeln (z. B. vorbelegte Felder, Idempotenz-Entscheidung) als reine Funktionen in `domain/conversion.py`.
2. Entscheidung `promote` aus TASK-010 an `ConversionService.promote` anschließen (wird hier statt `decision_not_available` ausgeführt; der Hinweis ist danach entschieden).
3. Route `POST /api/v2/notes/{project}/{label}/promote` Body `{version, item_type, title?, summary?, area, goal, completion_criteria, parent?, required_for_parent?, priority?, dependencies?}` → `{note: NoteOut, item: …}` mit dem Item in der Form der vorhandenen Item-Antworten. `project` ist der Projektname; das Item entsteht im Backlog **desselben** Projekts.
4. Verdrahtung in `bootstrap.py`/`container.py`, OpenAPI neu erzeugen.

## Dateien
`application/services/conversion.py` (neu), `domain/conversion.py` (neu), `application/container.py`, `bootstrap.py`, `api/v2/notes_routers.py`, `schemas.py`, Tests `backend/tests/unit/domain/test_conversion.py`, `tests/unit/application/test_conversion.py`, `tests/api_v2/test_promote.py`, Integrationsfall in `tests/integration/test_notes_flow.py`.

## Nicht anfassen
`ItemService`-Regeln, die Rückstufung (TASK-014), das UI-Formular (TASK-015), Datenmodell/Migrationen.

## Tests (zuerst)
Task/Story/Epic; Pflichtfeld fehlt → Fehler vom Backlog; geschlossener Parent → `parent_closed` und keine Note verändert; Dokumente und Langtext am Item; Note archiviert mit Status `promoted`; Link `origin` an Note und am Item abfragbar; Abbruch simulieren (Fake wirft in Schritt 4 oder 5) → Wiederholung erzeugt kein zweites Item, Endzustand wie im Normalfall; Markdown-Projekt und Datenbank-Projekt.

## Stoppen und fragen
Wenn `ItemService.create` den Titel anders erwartet, wenn die Dokumentnamen am Item nicht über `DocumentService` anlegbar sind oder wenn die Idempotenz über den `origin`-Link in einem Fall mehrdeutig ist (z. B. Item inzwischen gelöscht).

## Abnahme
Beförderung und Wiederholung per Test; Herkunft an Note und Item sichtbar; `scripts/check.sh` grün.
