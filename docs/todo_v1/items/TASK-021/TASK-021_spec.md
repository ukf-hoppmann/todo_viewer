# TASK-021 — Spec: Rotes Ausrufezeichen mit Zähler und Tab-Titel

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
Der Hinweis auf Aufmerksamkeit, ohne Popup. Kein Ton, keine Notification außerhalb der Seite.

## Schon vorhanden
- API (TASK-009): `GET /api/v2/notes-due/count` → `{count}`; das Icon ruft **nur** diese billige Abfrage, nicht die Liste.
- Header/Titel in `App.tsx`; Polling-Muster mit `POLL_INTERVAL_MS` und Pause über `state/pollingPause.ts` in `api/queries.ts`.
- Das Fällig-Modal ist TASK-022; hier öffnet der Klick einen Platzhalter-Zustand (`onOpen`-Callback), den TASK-022 füllt.

## Zu tun
1. `domain/notes.ts` (+ Test): `tabTitle(base, count)` → `"(3) ToDo-Viewer"` bzw. ohne Zahl bei 0; `badgeLabel(count)` (z. B. `99+` ab 100).
2. `api/queries.ts`: `useDueCount()` mit `refetchInterval: 60_000` (pausierbar wie das Backlog-Polling) und `refetchOnWindowFocus: true`.
3. `components/DueBadge.tsx`: Button mit rotem Ausrufezeichen (SVG, `aria-label` lokalisiert, Zahl), nur gerendert wenn `count > 0`. Dezent: kleine Größe, kein Blinken. Platz neben dem Titel oben links in `App.tsx`/`Sidebar.tsx`.
4. Tab-Titel: Effekt in `App.tsx`, der `document.title = tabTitle(...)` setzt und beim Verlassen zurücksetzt.
5. i18n-Texte (Keys englisch), Stile in `styles.css`.

## Dateien
`web/src/domain/notes.ts`, `notes.test.ts`, `api/queries.ts`, `components/DueBadge.tsx` (neu), `App.tsx` (oder `Sidebar.tsx`), `styles.css`, `i18n/messages.ts`, Test `web/src/components/notes.test.tsx`.

## Nicht anfassen
Das Modal-Innere (TASK-022), Backend, andere Header-Elemente.

## Tests
Unit: `tabTitle` bei 0, 1, 99, 100. Komponente: Icon nur bei Zähler > 0; Zähler wird angezeigt; Klick ruft `onOpen`. Abfrage-Verhalten: mit Fake-Timer wird nach 60 s erneut gefragt (Muster der vorhandenen Polling-Tests, falls vorhanden; sonst Query-Optionen direkt prüfen); Fokus-Refetch aktiv.

## Stoppen und fragen
Wenn das Pausieren des Pollings (`pollingPause`) auch den Zähler stoppen soll (Standard: ja, wie das Backlog), oder wenn der Header keinen Platz neben dem Titel hat.

## Abnahme
Icon erscheint/verschwindet manuell geprüft (Note mit Zeit-Auslöser anlegen, Zeitpunkt in die Vergangenheit setzen); Tab-Titel zeigt die Zahl (Screenshot); `scripts/check.sh` grün.
