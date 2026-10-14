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
Notes im vorhandenen Sync-Dialog bedienen (STORY-047). Es gibt keinen eigenen Notes-Dialog und keine eigene Schaltfläche.

## Schon vorhanden
- Gemeinsame Sync-API mit Notes (TASK-026), Konflikt-Dialog (STORY-058), `components/SyncDialog.tsx`, `domain/sync.ts` (+ `sync.test.ts`), `settings/ProjectsSection.tsx`, Hooks für den Sync in `api/queries.ts`.
- Hinweis: `ProjectsSection.tsx` und `styles.css` können uncommittete Änderungen haben; vorher `git status` prüfen und nichts davon verwerfen.

## Zu tun
1. `domain/sync.ts` (+ Test): `summarizePreview` zählt auch Topics, Notes und Note-Dokumente; die Konfliktzahl umfasst Notes.
2. `SyncDialog.tsx`: Abschnitte für Topics, Notes und Note-Dokumente in der Vorschau (neu, geändert, unverändert, nur im Ziel).
3. Konflikt-Dialog (STORY-058) um die Darstellung von Note- und Topic-Konflikten erweitern: Felder nebeneinander, Langtext und Note-Dokumente als Textvergleich.
4. Statussymbol in der Sidebar und in `ProjectsSection.tsx`: braucht keinen neuen Code, wenn der Status schon gemeinsam ist (TASK-026); sonst anpassen.
5. i18n-Texte (Keys englisch).

## Dateien
`web/src/components/SyncDialog.tsx`, Konflikt-Komponenten aus STORY-058, `settings/ProjectsSection.tsx`, `web/src/domain/sync.ts` (+ Test), `api/queries.ts`, `i18n/messages.ts`, Test `web/src/components/sync.test.tsx` (Ergänzung).

## Nicht anfassen
Backend, die Mechanik des Konflikt-Dialogs (nur um Notes erweitern).

## Tests
Unit: `summarizePreview` mit Notes, Konfliktzahl. Komponenten: Vorschau zeigt Topics, Notes und Note-Dokumente; Note-Konflikt erscheint im Konflikt-Dialog mit Textvergleich; Ausführen erst nach Vorschau; Fehler (`mirror_conflict`, `sync_stale`) wird als Text angezeigt; Statussymbol bei extern geänderter Notes-Datei.

## Stoppen und fragen
Wenn `ProjectsSection.tsx` mit den uncommitteten Änderungen kollidiert oder wenn der Konflikt-Dialog aus STORY-058 Note-Felder nicht generisch darstellen kann.

## Abnahme
Manuell: Projekt mit Spiegel-Ordner, Vorschau, Export und Import einer Note einmal durchspielen, einen Notes-Konflikt entscheiden (Screenshot); Tests grün; `scripts/check.sh` grün.
