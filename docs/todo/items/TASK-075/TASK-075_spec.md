# TASK-075 — Spec: Item oder Memo im Detail eines Knotens anlegen (Oberfläche)

Zu `STORY-103`. Der Server liefert `create_item_at_node` und `create_memo_at_node` (Task „Server: aus einem Knoten
ein Item oder ein Memo anlegen“).

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/client.md`. Tests und Befehle: `tests/README.md`; Client-Tests unter `tests/implementation/unit/client/…` (Vitest, Testing Library), Hilfen unter `tests/helpers/client/`. Am Ende laufen `cd client && npx tsc -b && npm run lint` und alle Client-Tests grün.

## Umfang

- Ort: das Detail eines Knotens in `client/src/plugins/mindmap/` (`NodeDetail.tsx`, Abschnitte
  `NodeContentSection.tsx`, `ItemNodeSection.tsx` als Vorbild für die Mutationen und das Fehlerbild).
- API: `client/src/plugins/mindmap/api.ts` (RTK Query): zwei Mutationen für die neuen Operationen; die Typen kommen
  aus `client/src/shared/api/schema.d.ts` (generiert, nicht von Hand). Tags so setzen, dass Baum, Inhalt des Knotens
  und Item-Zuordnung neu laden (`Tree`, `Content`, `ItemNode`, siehe `index.ts`).
- Dialoge: ein Dialog je Art, im Stil der übrigen Dialoge des Plugins (`BranchDialog.tsx`, `NodeMenus.tsx`).
  Item: Typ (Epic, Story, Task; keine Vorgabe), Titel, Ziel, Abschlusskriterien (Pflicht), optional Priorität
  (Standard Normal). Memo: Zusammenfassung, Text.
- Der Abschnitt zeigt keine Hinweise zur Ebene; die Wahl des Typs ist frei (Entscheidung des Owners).
- Testkennungen in `testIds.ts`; Übersetzungen `locales/de.json` und `en.json`.
- Das Muster für Eingabefelder und Fehleranzeige aus `client/src/shared/` verwenden (nichts nachbauen, was dort
  liegt).

## Tests

`tests/implementation/unit/client/plugins/mindmap/` (neben den vorhandenen Tests): Vorschläge im Dialog, Pflicht der
Kriterien, Aufruf der Mutation mit den richtigen Feldern, Fehler bleibt im Dialog, Knoten im Papierkorb ohne Aktion.

## Nicht Teil

Ganze Äste (nächste Task).
