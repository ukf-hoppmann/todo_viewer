# TASK-018 — Spec: Notes-Bereich: Gerüst, Topic-Baum und Notes-Liste

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
Das Gerüst des Bereichs Notes (STORY-045). Detailansicht (TASK-019), Auslöser (TASK-020), Ausrufezeichen (TASK-021), Modal (TASK-022), Item-Verknüpfung und Einstellungen (TASK-023) folgen.

## Schon vorhanden
- Backend-Routen aus TASK-004, TASK-005, TASK-006, TASK-009: `GET /api/v2/notes-index` (Topics + Notes, ohne Langtexte), Topic- und Note-CRUD, Löschen/Wiederherstellen, `GET /api/v2/notes/{project}/trash`.
- App-Rahmen in `App.tsx` mit Ansichten (`views/TreeView.tsx`, `KanbanView.tsx`, `GraphView.tsx`, `TrashView.tsx`) und Seitenleiste `components/Sidebar.tsx`; Projektliste über `useSourceList`.

## Zu tun
1. `web/src/domain/notes.ts` (+ `notes.test.ts`): `buildTopicTree(topics)`, `notesOfTopic(notes, topicLabel, includeSubtopics)`, `topicPath(topics, label)`, `sortNotes(notes)` (fällig zuerst, dann nach `review_at`). Reine Funktionen auf den generierten Typen.
2. `api/queries.ts`: `useNotesIndex(project?, filters?)`, `useCreateTopic`, `useUpdateTopic`, `useMoveTopic`, `useDeleteTopic` (mit Kaskade), `useCreateNote`, `useUpdateNote`, `useDeleteNote`. Nach Änderungen Cache `["notes-index"]` ungültig machen. Polling wie beim Backlog (`POLL_INTERVAL_MS`, pausierbar über `state/pollingPause.ts`).
3. `views/NotesView.tsx`: Layout zweispaltig. Links `components/TopicTree.tsx` (Baum, Auswahl, Anlegen/Umbenennen/Verschieben/Löschen über Kontextmenü oder Buttons, Tiefe wird vom Server geprüft: Fehlertext anzeigen), rechts `components/NoteList.tsx` (Zeile: Kurzfassung, Status-Badge, Fälligkeit, Grund). Projektfilter: das Projekt der Seitenleiste oder „alle“.
4. `components/NoteCreateDialog.tsx`: Kurzfassung (Pflicht, eine Zeile), Langtext optional, Topic; Muster `CreateItemDialog`.
5. Navigation: Eintrag „Notes“ in `Sidebar.tsx`/`App.tsx` neben dem Backlog; Auswahl (Projekt, Topic) über `state/useUiStateStore.ts` merken.
6. `i18n/messages.ts`: alle neuen Texte (Keys englisch).

## Dateien
`web/src/domain/notes.ts`, `notes.test.ts`, `api/queries.ts`, `views/NotesView.tsx`, `components/TopicTree.tsx`, `NoteList.tsx`, `NoteCreateDialog.tsx`, `Sidebar.tsx`, `App.tsx`, `state/useUiStateStore.ts`, `i18n/messages.ts`, `styles.css`, Test `web/src/components/notes.test.tsx` (neu).

## Nicht anfassen
Detailansicht und Dokumente (TASK-019), Auslöser (TASK-020), Ausrufezeichen/Modal (TASK-021/TASK-022), `schema.d.ts`/`openapi.json`, Backend.

## Tests
Unit: Baumbau (Tiefe 3, Waisen), Teilbaum-Filter, Sortierung. Komponenten: Baum rendert, Auswahl filtert die Liste, Anlegen ruft die Route, Server-Fehler (`topic_depth_exceeded`) erscheint als Text.

## Stoppen und fragen
Wenn TASK-009 (`notes-index`) Felder nicht liefert, die die Liste braucht, oder wenn `App.tsx` keinen Platz für einen zweiten Bereich ohne größeren Umbau lässt.

## Abnahme
Anlegen, Auswählen, Ändern, Verschieben, Löschen manuell geprüft (Screenshot), Unit- und Komponententests grün; `scripts/check.sh` grün.
