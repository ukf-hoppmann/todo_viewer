# TASK-015 — Spec: UI-Dialoge für Beförderung und Rückstufung

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-042), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
UI zu TASK-013 und TASK-014. Die UI ist nur Client der API v2 (`architecture/web.md` §1): alle Requests nur in `web/src/api/`.

## Schon vorhanden
- Dialoge als Muster: `components/CreateItemDialog.tsx` (Formular, Vorbelegung, Fehleranzeige), `RetypeDialog.tsx`, `DeleteDialog.tsx`, `Modal.tsx`.
- Notes-Bereich und Detailansicht der Note aus TASK-018/TASK-019, Hooks in `api/queries.ts`, Texte in `i18n/messages.ts` (Keys englisch).
- API: `POST /api/v2/notes/{project}/{label}/promote`, `POST /api/v2/items/{source_id}/{item_id}/demote` (TASK-013, TASK-014), generierte Typen in `api/schema.d.ts`.

## Zu tun
1. Hooks `usePromoteNote`, `useDemoteItem` in `api/queries.ts` (Cache der Notes und des Backlogs danach ungültig machen).
2. `components/PromoteNoteDialog.tsx`: Felder wie `CreateItemDialog` (Typ, Bereich, Ziel, Abschlusskriterien, Parent, Priorität), Titel und Zusammenfassung aus der Kurzfassung vorbelegt, Ziel aus dem Langtext, wenn vorhanden. Eingebunden in der Note-Detailansicht (Aktion „Befördern“) und später im Fällig-Modal (TASK-022).
3. `components/DemoteItemDialog.tsx`: Bestätigung mit Hinweis, was passiert (Item wird abgeschlossen, Notizen und Specs wandern an die Note), optionales Topic; im `DetailPanel` nur bei Status Open sichtbar. Ablehnungscodes (`demote_not_open`, `demote_has_children`, `demote_referenced`, `parent_closed`) mit Texten in `i18n` (Keys englisch, Anzeige Deutsch/Englisch wie vorhanden).
4. Herkunft anzeigen: an der Note und am Item der Link `origin` als „Aus Note NOTE-001“ / „Herkunft Item …“ mit Sprung dorthin (eine kleine Komponente, im `DetailPanel` und in der Note-Detailansicht verwendet).
5. Nach Erfolg zur neuen Note bzw. zum neuen Item navigieren oder den Dialog mit Link schließen (Muster der vorhandenen Dialoge).

## Dateien
`web/src/components/PromoteNoteDialog.tsx`, `DemoteItemDialog.tsx`, `OriginLink.tsx` (neu), `DetailPanel.tsx`, die Note-Detailansicht aus TASK-019, `api/queries.ts`, `i18n/messages.ts`, Tests `web/src/components/conversion.test.tsx` (neu).

## Nicht anfassen
`api/schema.d.ts` und `openapi.json` (generiert), Fällig-Modal selbst (TASK-022), Backend.

## Tests
Komponententest wie `components.test.tsx`: Formular vorbelegt; Absenden ruft die Route mit den Feldern; Fehlercode wird als lokalisierter Text gezeigt; Rückstufen-Aktion nur bei Status Open; Herkunftslink erscheint. Test-first nicht nötig (UI), aber vor Abschluss grün.

## Stoppen und fragen
Wenn TASK-019 noch nicht fertig ist (Detailansicht fehlt), wenn die generierten Typen von TASK-013/TASK-014 nicht vorliegen, oder wenn das Formular Felder verlangt, die `CreateItemDialog` nicht kennt.

## Abnahme
Beide Dialoge manuell gegen die laufende App geprüft (Screenshot genügt) und per Komponententest; `scripts/check.sh` grün.
