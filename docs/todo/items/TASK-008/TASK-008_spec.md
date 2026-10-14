# TASK-008 — Spec: Dokumente einer Note: Notizen und Specs lesen und schreiben

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-039), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Wie `DocumentService` für Items, nur für Notes.

## Schon vorhanden
- Port `NoteDocumentStore` (`application/ports.py`): `names`, `read`, `write(project, label, name, content, expected_version)`, `append(project, label, name, text, header)`, `delete_document`; Implementierung `DatabaseNoteDocumentStore` in `infrastructure/database/notes.py`.
- `check_note_document_name(label, name)` in `domain/notes.py` (erlaubt `<LABEL>_notes.md`, `<LABEL>_spec.md`, `<LABEL>_spec_<topic>.md`).
- Vorbild: `application/services/documents.py` (`DocumentService.write`, `append_notes`) und die Item-Routen `GET/PUT /items/{source_id}/{item_id}/documents/{name}` sowie `POST …/notes` in `api/v2/routers.py`.
- Der `NoteService` kennt den `NoteDocumentStore` noch nicht; `bootstrap.py` muss ihn übergeben.

## Zu tun
1. Neuer Service `NoteDocumentService` in `application/services/note_documents.py` (nicht in `NoteService`): `read`, `write`, `append_notes(project, label, topic, discussed, decided, open)`, `names`. Er prüft zuerst, dass die Note existiert (`NoteNotFoundError`) und den Dateinamen. Das Datum eines Eintrags setzt der Service (nicht der Aufrufer), Format wie beim Backlog.
2. Versionstoken: wie beim Backlog (`version: <v>` aus dem Store); `write` mit `null` = Dokument darf noch nicht existieren.
3. In `container.py` und `bootstrap.py` verdrahten.
4. Routen (`tags=["note-documents"]`):
   - `GET /api/v2/notes/{project}/{label}/documents` → Liste der Namen.
   - `GET /api/v2/notes/{project}/{label}/documents/{name}` → `{name, version, content}`.
   - `PUT /api/v2/notes/{project}/{label}/documents/{name}` Body `{content, version|null}` → `{name, version}`.
   - `POST /api/v2/notes/{project}/{label}/notes` Body `{topic, discussed[], decided[], open[]}` → hängt einen datierten Eintrag an `<LABEL>_notes.md` an.
5. OpenAPI neu erzeugen.

## Dateien
`application/services/note_documents.py` (neu), `application/services/__init__.py`, `application/container.py`, `bootstrap.py`, `api/v2/notes_routers.py`, `api/v2/schemas.py`, Tests `backend/tests/api_v2/test_note_documents.py` (neu), `tests/unit/application/test_note_documents.py` (neu, gegen den Datenbank-Store auf einer temporären SQLite-Datei wie `test_note_service.py`).

## Nicht anfassen
Den Item-`DocumentService`, die Dokument-Tabelle, die Markdown-Spiegelung (STORY-047).

## Tests (zuerst)
Neu anlegen (`version: null`), lesen, ersetzen mit richtigem Token, ersetzen mit altem Token → 409, ungültiger Name → `document_forbidden`, fehlendes Dokument → 404, Anhängen legt die Datei beim ersten Mal an und schreibt Datum und die drei Abschnitte `Discussed`/`Decided`/`Open`, Note existiert nicht → 404.

## Stoppen und fragen
Wenn das Eintragsformat beim Anhängen vom Backlog abweicht oder `append` des Stores den Header anders erwartet.

## Abnahme
Alle Routen per API-Test inklusive Versionskonflikt; `scripts/check.sh` grün.
