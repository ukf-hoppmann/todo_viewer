# TASK-020 — Spec: Notes-Bereich: Auslöser anzeigen, bearbeiten und Zurückstellen

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
Auslöser und Zurückstellen in der Notes-UI.

## Schon vorhanden
- API (TASK-006): `POST /api/v2/notes/{project}/{label}/triggers` (`kind`: time|event|topic_due, `at`, `target`, `target_status`), `DELETE …/triggers/{id}`, `POST …/snooze` (`version`, `review_at?`, `trigger?`). Der Server meldet bei Ereignissen mit schon erreichtem Ziel `already_met`.
- TASK-019: `NoteDetail` mit Platz für die Aktionen. `NoteOut.triggers`, `fired`, `all_fired`.
- Backlog-Items zur Auswahl: `useBacklog` (alle Quellen und Items), Index `GET /api/v2/index`.
- Zeiten sind UTC im Speicher; Anzeige und Eingabe in der Zeitzone des Rechners (`Intl`, `datetime-local`).

## Zu tun
1. `domain/notes.ts` (+ Test): `snoozePresets(now)` → morgen früh (08:00 lokal), in einer Woche, in 30 Tagen; `toIsoWithZone(localDateTimeString)`; `describeTrigger(trigger)` (Text-Schlüssel + Parameter); `alreadyMet(item, targetStatus)` (nutzt den Status aus dem Backlog, damit die UI **vor** dem Speichern warnen kann; der Server bleibt maßgeblich).
2. `components/TriggerEditor.tsx`: Liste der Auslöser (Art, Ziel, gefeuert/offen) mit Entfernen; Anlegen-Formular je Art: Zeit (Datum + Uhrzeit), Ereignis (Projekt → Item wählen, Zielstatus aus In progress / Awaiting confirmation / Completed / Rejected; Hinweis „bereits erreicht“ vor dem Speichern), Topic-Termin (nur wenn die Note ein Topic mit Termin hat, sonst Hinweistext). Der Modus-Schalter any/all wird **nicht** angezeigt; das Feld bleibt unberührt.
3. `components/SnoozeDialog.tsx`: Schnellwahlen (siehe 1), eigenes Datum, optional ein neuer Ereignis-Auslöser (derselbe Formularteil wie im Editor). Nutzt `useSnoozeNote`.
4. Topic-Termin am Topic setzen: kleines Feld im Topic-Menü von TASK-018 (`due_at`), Hook `useUpdateTopic` ist da.
5. Hooks: `useAddTrigger`, `useRemoveTrigger`, `useSnoozeNote`.
6. i18n-Texte (Keys englisch).

## Dateien
`web/src/domain/notes.ts`, `notes.test.ts`, `components/TriggerEditor.tsx`, `SnoozeDialog.tsx` (neu), `NoteDetail.tsx`, `TopicTree.tsx` (Termin-Feld), `api/queries.ts`, `i18n/messages.ts`, `components/notes.test.tsx`.

## Nicht anfassen
Den Modus any/all (nicht bedienbar), das Fällig-Modal (TASK-022, nutzt `SnoozeDialog`), Backend.

## Tests
Unit: Schnellwahlen mit festem „jetzt“ (auch Monats-/Jahreswechsel, Sommerzeit), ISO-Umwandlung mit Zeitzone, `alreadyMet`. Komponenten: Zeit-Auslöser anlegen, Ereignis mit bereits erreichtem Ziel zeigt die Warnung, Entfernen, Zurückstellen sendet das richtige Datum, Modus-Schalter fehlt.

## Stoppen und fragen
Wenn die Zeitzone des Rechners nicht verlässlich ermittelbar ist (Test auf anderer Zone), oder wenn `useBacklog` für die Itemauswahl zu schwer ist (dann Index-Route nutzen).

## Abnahme
Alle drei Auslöser-Arten und Zurückstellen manuell geprüft (Screenshot) und per Test; `scripts/check.sh` grün.
