# TASK-070 — Spec: Oberfläche ohne Area

Zu `STORY-106`. Voraussetzung: `area` ist am Server kein Pflichtfeld mehr (Task „Area ist beim Anlegen nicht mehr
Pflicht“).

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/client.md`. Tests und Befehle: `tests/README.md`; Client-Tests unter `tests/implementation/unit/client/…` (Vitest, Testing Library), Hilfen unter `tests/helpers/client/`. Am Ende laufen `cd client && npx tsc -b && npm run lint` und alle Client-Tests grün.

## Umfang

- `client/src/plugins/backlog/ItemForm.tsx`: Zustand `area`, die Auswahl aus `useListAreasQuery`, das Pflichtfeld
  samt `form.areaHint`; die `fields` für Anlegen und Ändern ohne `area`.
- `client/src/plugins/backlog/ItemDetail.tsx`: der Wert „Bereich“ (Auswahl mit `NEW_AREA`), der Prompt-Dialog
  `prompt === "area"` mit `TextPromptDialog`, `areaNames`, `useListAreasQuery`. `TextPromptDialog` bleibt (die
  Auflösung nutzt ihn weiter); nur sein Kommentar nennt den Bereich.
- `client/src/plugins/backlog/api.ts`: `listAreas` und `useListAreasQuery` (Export) entfernen.
- `client/src/plugins/memos/PromoteDialog.tsx`: Feld `area` samt Pflicht; die Felder der Beförderung sind `goal`
  und `completion_criteria`.
- Übersetzungen: `client/src/plugins/backlog/locales/{de,en}.json` (`field.area`, `area.*`, `form.areaHint`,
  `newArea`) und `client/src/plugins/memos/locales/{de,en}.json` (`promote.area`).
- Nicht entfernen: `areaOf` in `backlog/model.ts` und `memos/model.ts` sowie die Eigenschaft `area` von
  `TreeView` in `client/src/shared/tree/` — das ist eine hinterlegte Fläche im Baum und hat mit dem Feld nichts zu
  tun.
- Die Typen in `client/src/shared/api/schema.d.ts` bleiben (das Feld `area` ist am Server noch da); der Client
  liest und sendet es nur nicht mehr.
- Das Thema eines Items zeigt schon der Abschnitt `ItemNodeSection` (`client/src/plugins/mindmap/`); dort ist
  nichts zu bauen, nur zu prüfen, dass er im Detail bleibt.

## Tests

`tests/helpers/client/backlogFixtures.ts`; `tests/implementation/unit/client/plugins/backlog/` (`ItemEditing`,
`ItemDetail`, `BacklogPage`, `model`) und `…/memos/` (`MemosPage`, Beförderung) anpassen: kein Feld Area, kein
Aufruf von `backlog/areas`.
