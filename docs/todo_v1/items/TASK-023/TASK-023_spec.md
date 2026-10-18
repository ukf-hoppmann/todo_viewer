# TASK-023 — Spec: Verlinkte Notes am Backlog-Item und Notes-Einstellungen

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
Notes vom Item aus erreichen und die zwei Notes-Optionen bedienen.

## Schon vorhanden
- API: `GET /api/v2/links-to?kind=item&project=…&label=…` (TASK-007; kompakt: Projekt, Label, Kurzfassung, Status, Rolle), `GET /api/v2/notices?side=item&project=…&label=…&open=true` und `POST /api/v2/notices/{id}/decision` mit `acknowledge` (TASK-010/TASK-012), `GET/PUT /api/v2/notes-settings` (TASK-009).
- `components/DetailPanel.tsx` (Item-Detail), `components/settings/GeneralSection.tsx` (Abschnitt „Allgemein“) und `settings/sections.tsx`.
- Die Item-ID im Detail ist das Item-Label; das Projekt ist der Projektname der Quelle (nicht die Quell-ID!).

## Zu tun
1. `api/queries.ts`: `useNotesLinkedToItem(project, itemLabel)`, `useItemNotices(project, itemLabel)`, `useAcknowledgeNotice`, `useNotesSettings`, `useSaveNotesSettings`.
2. `components/ItemNotes.tsx` im `DetailPanel`: Abschnitt „Notes“, Liste der verlinkten Notes (Kurzfassung, Status-Badge, Rolle, bei anderem Projekt „Projekt · Label“), Klick wechselt in den Bereich Notes zur Note. Leere Liste → Abschnitt ausblenden. Offene Hinweise (z. B. „Note NOTE-004 wurde verworfen“) mit Button „Zur Kenntnis nehmen“.
3. `domain/notes.ts` (+ Test): `describeNotice(notice)` (Text-Key + Parameter), `sortLinkedNotes(notes)` (offene vor erledigten).
4. `components/settings/GeneralSection.tsx`: zwei Zahlfelder `review_days` (1–3650) und `max_topic_depth` (1–10), Standardwerte als Platzhalter, Speichern über den Hook, Serverfehler (`invalid_value`) lokalisiert anzeigen, Hinweis, dass die Tiefe vorhandene Topics nicht ändert.
5. i18n-Texte (Keys englisch).

## Dateien
`web/src/components/ItemNotes.tsx` (neu), `DetailPanel.tsx`, `components/settings/GeneralSection.tsx`, `web/src/domain/notes.ts`, `notes.test.ts`, `api/queries.ts`, `i18n/messages.ts`, Tests `web/src/components/notes.test.tsx`, `settings.test.tsx`.

## Nicht anfassen
Backend, Dialoge aus TASK-019/TASK-020, die übrigen Einstellungsabschnitte.

## Tests
Unit: Sortierung, `describeNotice`. Komponenten: Item mit zwei verlinkten Notes aus zwei Projekten, leere Liste blendet den Abschnitt aus, Hinweis wird zur Kenntnis genommen; Einstellungen laden, speichern, ungültiger Wert zeigt Fehler.

## Stoppen und fragen
Wenn `DetailPanel` das Projekt des Items nur als Quell-ID kennt (Projektname fehlt), oder wenn TASK-012 noch fehlt (dann ohne Hinweise bauen und melden).

## Abnahme
Manuell: Note mit Link auf ein Item anlegen, im Item-Detail sehen, hineinspringen; Einstellungen ändern und neu laden (Screenshot); `scripts/check.sh` grün.
