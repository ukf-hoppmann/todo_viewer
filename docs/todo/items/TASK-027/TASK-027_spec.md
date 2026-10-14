# TASK-027 — Spec: Notes-Sync im Einstellungsmenü bedienen

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-047), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
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
Bedienung des Notes-Syncs (STORY-047) in der UI.

## Schon vorhanden
- API (TASK-026): `GET /api/v2/sources/{source_id}/notes-sync-status`, `POST /api/v2/sources/{source_id}/notes-sync` (`direction`, `dry_run`, `decisions`, `confirm_delete`).
- `components/SyncDialog.tsx` (Vorschau, Richtung, Bestätigung des Backlog-Syncs), `domain/sync.ts` (+ `sync.test.ts`), `settings/ProjectsSection.tsx`, Hooks für den Backlog-Sync in `api/queries.ts`.
- Hinweis: `ProjectsSection.tsx` und `styles.css` haben in der Arbeitskopie uncommittete Änderungen; vorher `git status` prüfen und nichts davon verwerfen.

## Zu tun
1. `domain/sync.ts` (oder neu `domain/notesSync.ts`, + Test): `summarizePreview(preview)` (Zählungen), `needsDecision(preview)`, `canRun(preview, decisions, confirmDelete)`.
2. Hooks: `useNotesSyncStatus(sourceId)`, `useNotesSyncPreview`, `useRunNotesSync`.
3. `components/NotesSyncDialog.tsx` (oder Erweiterung von `SyncDialog` als zweiter Reiter, je nachdem, was das kleinere Risiko ist; bevorzugt eigener Dialog, der Layout und Textbausteine des `SyncDialog` wiederverwendet): Richtung, Vorschau-Tabelle (neu/geändert/unverändert/nur im Ziel/Kollision), Entscheidung je Kollision (`keep_db`, `take_mirror`, `import_as_new`), Checkbox „Im Ziel löschen“ nur wenn die Vorschau Einträge „nur im Ziel“ enthält, Ausführen erst nach Vorschau.
4. In `settings/ProjectsSection.tsx` je Projekt mit Spiegel-Ordner: Button „Notes abgleichen“ und das Statussymbol „Spiegel extern geändert“.
5. i18n-Texte (Keys englisch).

## Dateien
`web/src/components/NotesSyncDialog.tsx` (neu), `settings/ProjectsSection.tsx`, `web/src/domain/` (Funktionen + Test), `api/queries.ts`, `i18n/messages.ts`, Test `web/src/components/sync.test.tsx` (Ergänzung).

## Nicht anfassen
Den Backlog-Sync-Dialog (außer geteilten Textbausteinen), Backend.

## Tests
Unit: `summarizePreview`, `needsDecision`, `canRun`. Komponenten: Vorschau wird geladen, Ausführen ist gesperrt bis alle Kollisionen entschieden sind, Löschen verlangt die Checkbox, Konfliktfehler (`mirror_conflict`) wird als Text angezeigt, Statussymbol bei externer Änderung.

## Stoppen und fragen
Wenn `ProjectsSection.tsx` mit den uncommitteten Änderungen kollidiert oder wenn ein Projekt ohne Spiegel-Ordner den Button zeigen soll.

## Abnahme
Manuell: Projekt mit Spiegel-Ordner, Vorschau, Export und Import einer Note einmal durchspielen (Screenshot); Tests grün; `scripts/check.sh` grün.
