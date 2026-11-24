# TASK-075 — Oberfläche: im Detail eines Knotens ein Item oder Memo anlegen

## State

- Goal/Status: Umgesetzt und verifiziert; wartet auf die Abnahme des Owners.
- Next step: Abnahme durch den Owner; danach `TASK-076` (Ast im Dialog), das auf `TASK-074` und diese Task aufbaut.
- Open:
  - Nichts offen (2026-11-24)
- Decided:
  - Es gibt keine Typvorgabe im Dialog; der Mensch wählt den Typ (Owner) (2026-11-23)
  - Die Buttons „Item anlegen“ und „Memo anlegen“ stehen im Abschnitt „Items und Memos“ des Knoten-Details (`NodeContentSection`), die Dialoge in `CreateFromNodeDialogs.tsx` (2026-11-24)
  - Ein Knoten im Papierkorb hat kein Detail, daher keine Aktion und kein eigener Zweig dafür im Code (2026-11-24)
  - Priorität und Typ-Liste kommen aus dem öffentlichen Index von `backlog` (`PRIORITIES`, `TYPES`), nicht kopiert (2026-11-24)
- References: Spec `TASK-075_spec.md`; Story `STORY-103` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: TASK-073

State confirmed after entry 2026-11-24 — Umsetzung (8e509b65e1e2)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-103

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-103 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-103_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Es gibt keine Typvorgabe im Dialog; der Mensch wählt den Typ (Owner)

### Open

- Nichts.

## 2026-11-24 — Umsetzung

### Discussed

- Plan nach der Zerlegungsregel: 1. Fake-Server der Tests um die beiden Operationen erweitern, 2. Test zuerst (Dialoge, Pflichtfelder, Aufruf, Fehler im Dialog), 3. Mutationen, Dialoge, Buttons, Testkennungen und Übersetzungen, 4. Doku, 5. Integration (Typen, Lint, alle Tests).
- Der Knoten im Papierkorb: `NodeOut` trägt kein Merkmal „gelöscht“, und die Seite öffnet das Detail nur für Knoten des lebenden Baums. Es gibt also keinen Zustand, in dem das Detail eines gelöschten Knotens eine Aktion anböte; ein Test dafür hätte nichts zu prüfen.
- `PRIORITIES` und `TYPES` standen nur in `backlog/constants.ts`. Statt sie zu kopieren, exportiert der Index von `backlog` sie (eine Zeile).
- Der Lint meldete 5 Fehler in `core/ui-state/usePersistentState.ts` (Ref beim Rendern gelesen), schon vor dieser Task. Weil Lint zu den Kriterien gehört und die Korrektur klein und eindeutig ist (`useState` statt `useRef(...).current`, gleiches Verhalten), ist sie hier mit enthalten.

### Decided

- Buttons im Abschnitt „Items und Memos“, je einer unter dem Zuordnen- und dem Verlinken-Feld
- Der Dialog bleibt offen und behält die Eingaben, wenn der Server ablehnt; „Anlegen“ ist gesperrt, bis Typ, Titel und Abschlusskriterien da sind (Memo: Zusammenfassung)
- Das Ziel wird nur gesendet, wenn es nicht leer ist (sonst gilt der Text des Knotens ohnehin nicht, und das Backlog prüft)

### Open

- Nichts.
