# TASK-073 — Server: aus einem Knoten ein Item oder ein Memo anlegen

## State

- Goal/Status: Umgesetzt und verifiziert; wartet auf die Abnahme des Owners.
- Next step: Abnahme durch den Owner; danach `TASK-074` (Ast mit Vorschau) und die Oberfläche `TASK-075`.
- Open:
  - Nichts offen (2026-11-24)
- Decided:
  - Der Typ des Items wird nicht aus der Ebene abgeleitet; Mensch oder KI legt ihn je Knoten fest (Owner) (2026-11-23)
  - Ein Ideen-Knoten lässt sich auch zu einem Memo machen; ein Knoten mit nur einem Memo bleibt Idee, weil Memos nicht zählen (Owner) (2026-11-23)
  - Titel und Text des Knotens sind Standardwerte, Abschlusskriterien kommen immer vom Aufrufer, weil der Knoten keine hat (Zuschnitt) (2026-11-23)
  - Die Ports liefern `CreatedElement` (uid, Label, Titel, Typ) statt nur der uid, damit die Antwort ohne weiteren Zugriff auf andere Plugins auskommt (2026-11-24)
  - Fehler beim Anhängen heißt `mindmap_assign_failed` mit `details.created` und `details.cause`; kein Rückbau (2026-11-24)
  - Die Importregeln brauchen keine Änderung: Adapter sprechen die Dienste von `backlog` und `memos` über `Any`, ohne deren Code zu importieren; neu ist nur `memos` in `requires` (2026-11-24)
- References: Spec `TASK-073_spec.md`; Story `STORY-103` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: TASK-071

State confirmed after entry 2026-11-24 — Umsetzung (63b1f474f4ae)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-103

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-103 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-103_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Der Typ des Items wird nicht aus der Ebene abgeleitet; Mensch oder KI legt ihn je Knoten fest (Owner)
- Ein Ideen-Knoten lässt sich auch zu einem Memo machen; ein Knoten mit nur einem Memo bleibt Idee, weil Memos nicht zählen (Owner)
- Titel und Text des Knotens sind Standardwerte, Abschlusskriterien kommen immer vom Aufrufer, weil der Knoten keine hat (Zuschnitt)

### Open

- Nichts.

## 2026-11-24 — Umsetzung

### Discussed

- Ablauf nach der Zerlegungsregel: 1. Domain (Standardwerte, Pflicht der Kriterien), 2. Anwendungsfall mit Fakes der Ports (beides Test zuerst), 3. Adapter, Operationen und Verdrahtung mit Integrationstests, 4. Typen und Doku.
- Das Ergebnis braucht Label und Titel des Angelegten; die Ports geben darum ein `CreatedElement` zurück, nicht nur die uid der Spec.
- Die Antwort zeigt den Knoten als `TreeNodeOut` (mit `state`), weil `NodeOut` keinen Zustand hat und die Spec ihn verlangt.
- Der Knoten wird vor dem Anlegen geprüft (`MindmapService.node_for_creation`: lebend, bei genanntem Projekt aus diesem), damit ein abgewiesener Aufruf nichts anlegt.

### Decided

- Ports `BacklogWriter`, `MemoWriter` liefern `CreatedElement`; Fehler beim Anhängen als `mindmap_assign_failed` mit `details.created`
- Keine Änderung an `[tool.importlinter]`: kein Code-Import zwischen den Plugins, nur `requires` und Dienste über `Any`

### Open

- Nichts.
