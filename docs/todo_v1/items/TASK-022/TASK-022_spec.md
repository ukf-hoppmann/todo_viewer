# TASK-022 — Spec: Fällig-Modal mit Gruppierung und Aktionen

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
Arbeitsliste für alles, was Aufmerksamkeit braucht.

## Schon vorhanden
- API: `GET /api/v2/notes-due` → Liste mit `project`, `label`, `summary`, `reason` (`trigger`, `review_expired`, `topic_due`, `notice`), `fired`, `actions[]`; Aktionen: `POST …/snooze`, `POST …/finish` (`done`/`dropped`), Beförderung `POST …/promote`, Hinweis-Entscheidungen `POST /api/v2/notices/{id}/decision` (`keep`, `detach`, `drop`, `promote`).
- UI-Teile: `DueBadge` (TASK-021, `onOpen`), `SnoozeDialog` (TASK-020), `PromoteNoteDialog` (TASK-015), `Modal.tsx`, `NotesView` zum Öffnen einer Note.

## Zu tun
1. `domain/notes.ts` (+ Test): `groupDueByReason(items)` (feste Reihenfolge der Gruppen: Auslöser, Änderungshinweis, Termin, Prüfung), `rowActions(item)` (welche Aktionen eine Zeile anbietet; Hinweise ergänzen `keep`/`detach`), `nextAfterAction(...)` (welche Zeile nach einer Aktion fokussiert wird).
2. `api/queries.ts`: `useDueList()` (nur wenn das Modal offen ist, kein Dauer-Polling) und Aktions-Hooks aus TASK-019/TASK-020/TASK-015/TASK-010; nach jeder Aktion Zähler (`notes-due/count`) und Liste ungültig machen.
3. `components/DueModal.tsx`: Gruppen mit Überschrift und Anzahl; Zeile mit Kurzfassung, Projekt, Topic-Pfad, Grund-Detail (welcher Auslöser feuerte; bei Hinweisen die Ursache) und den Aktionsbuttons; „Zurückstellen“ öffnet `SnoozeDialog`, „Befördern“ `PromoteNoteDialog`, „Öffnen“ wechselt in den Bereich Notes zur Note und schließt das Modal.
4. Das Modal bleibt offen, bis die Liste leer ist oder der Besitzer schließt; eine bearbeitete Zeile verschwindet erst, wenn die Aktion beim Server gelungen ist.
5. In `App.tsx` das Modal an `DueBadge.onOpen` anschließen.
6. i18n-Texte (Keys englisch).

## Dateien
`web/src/components/DueModal.tsx` (neu), `web/src/domain/notes.ts`, `notes.test.ts`, `api/queries.ts`, `App.tsx`, `i18n/messages.ts`, `styles.css`, Test `web/src/components/notes.test.tsx`.

## Nicht anfassen
Die Dialoge selbst (TASK-020, TASK-015), die Zählerabfrage (TASK-021), Backend.

## Tests
Unit: Gruppierung (leer, eine Gruppe, alle Gruppen, stabile Reihenfolge), Aktionen je Grund. Komponenten: Gruppen und Zeilen werden gerendert; „erledigen“ ruft `finish`, Zeile verschwindet erst nach Erfolg und bleibt bei Fehler samt Fehlermeldung; Hinweis-Zeile zeigt `keep` und `detach`; „Öffnen“ navigiert.

## Stoppen und fragen
Wenn TASK-010 (Hinweise) noch nicht fertig ist: ohne Hinweis-Gruppe bauen und das hier melden, die Gruppe folgt dann in einer eigenen kleinen Ergänzung. Auch bei fehlenden Feldern in `notes-due`.

## Abnahme
Manuell: fällige Note anlegen, Modal öffnen, jede Aktion einmal ausführen (Screenshot); Unit- und Komponententests grün; `scripts/check.sh` grün.
