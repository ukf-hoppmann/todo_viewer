# TASK-019 — Spec: Notes-Bereich: Detailansicht, Dokumente und Links

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-045), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Gilt für alle UI-Tasks dieser Story
- Die UI ist nur Client der API v2: HTTP-Aufrufe nur in `web/src/api/` (Hooks in `queries.ts`), Typen aus `schema.d.ts` (generiert, nie von Hand).
- Server-Daten halten TanStack-Query-Hooks, nicht Komponenten-State; dauerhafter UI-Zustand nur über `src/state/` und `/api/v2/ui-state`, nicht `localStorage`.
- Gruppieren, Zählen, Baumbau und Aktionsregeln sind **reine Funktionen** in `web/src/domain/notes.ts` mit Unit-Test (`notes.test.ts`), ohne React/DOM/Netz.
- Texte nur über `web/src/i18n/messages.ts`, Keys englisch (Muster der vorhandenen Keys), Anzeige in den vorhandenen Sprachen.
- Vorbilder: `components/DetailPanel.tsx`, `DocumentDialog.tsx`, `CreateItemDialog.tsx`, `Modal.tsx`, `views/TreeView.tsx`, `components/settings/*`.
- Prüfen im Browser: `preview_start` mit der Dev-Konfiguration aus `.claude/launch.json` (existiert sie nicht, anlegen), Screenshot als Beleg.

## Ziel
Detailansicht der Note im Bereich Notes (rechts neben oder statt der Liste, wie `DetailPanel` beim Backlog).

## Schon vorhanden
- TASK-018: `NotesView`, Hooks, `domain/notes.ts`.
- API: `GET/PATCH /api/v2/notes/{project}/{label}`, Links-Routen (TASK-007: `POST/GET /…/links`, `DELETE /…/links/{id}`, `GET /api/v2/links-to`), Dokumente (TASK-008: `GET/PUT /…/documents/{name}`, `POST /…/notes`).
- Vorbilder: `DetailPanel.tsx`, `DocumentDialog.tsx` (Dokument lesen/schreiben mit Versionstoken, Markdown-Anzeige mit DOMPurify), `ItemEditForm.tsx`.

## Zu tun
1. `components/NoteDetail.tsx`: Kurzfassung (eine Zeile) und Langtext (Markdown, Anzeige/Bearbeiten), Status, Fälligkeit mit Grund, Topic (wechselbar), Prüf-Datum (nur Anzeige). Speichern mit `version`; bei `version_conflict` Meldung mit „Neu laden“.
2. Aktionen in der Detailansicht, die schon ohne Auslöser möglich sind: erledigen, verwerfen (`finish`), „behalten“ (`keep`), löschen. Bestätigungsdialog nach Muster `DeleteDialog`. Zurückstellen und Befördern kommen mit TASK-020/TASK-022/TASK-015, hier nur der Platz dafür.
3. `components/NoteLinks.tsx`: Liste der Links (Rolle, Ziel als „Projekt · Label“, bei Items Titel/Status), Link hinzufügen (Item per Projekt + Label wählen; Topic; andere Note), Link lösen. Rollen `trigger`/`origin` nur anzeigen, nicht lösbar.
4. `components/NoteDocuments.tsx`: Dateien (`NOTE-001_notes.md`, `…_spec.md`, `…_spec_<topic>.md`) anzeigen und über den vorhandenen `DocumentDialog` bearbeiten; neuer Notizeintrag (Thema, Discussed/Decided/Open) wie beim Backlog. Den `DocumentDialog` nur parametrisieren (Lade-/Speichern-Funktion übergeben), nicht kopieren.
5. Hooks: `useNote`, `useNoteLinks`, `useAddLink`, `useRemoveLink`, `useNoteDocument`, `useWriteNoteDocument`, `useAppendNoteEntry`, `useFinishNote`, `useKeepNote`.
6. i18n-Texte (Keys englisch).

## Dateien
`web/src/components/NoteDetail.tsx`, `NoteLinks.tsx`, `NoteDocuments.tsx` (neu), `DocumentDialog.tsx` (Parametrisierung), `views/NotesView.tsx`, `api/queries.ts`, `i18n/messages.ts`, Tests in `web/src/components/notes.test.tsx`.

## Nicht anfassen
Auslöser-Editor (TASK-020), Zurückstellen, Ausrufezeichen und Modal (TASK-021/TASK-022), Backend.

## Tests
Komponenten: Detail rendert Felder; Speichern sendet `version`; Konfliktmeldung bei 409; Link hinzufügen/lösen; trigger-Link ohne Löschen-Button; Dokument lesen und speichern (Fake-Server wie in den vorhandenen Tests).

## Stoppen und fragen
Wenn sich `DocumentDialog` nicht ohne großen Umbau parametrisieren lässt (dann kleinen eigenen Dialog vorschlagen), oder wenn TASK-007/TASK-008 Felder nicht liefern, die die Anzeige braucht.

## Abnahme
Alle genannten Funktionen manuell geprüft (Screenshot) und per Komponententest; `scripts/check.sh` grün.
