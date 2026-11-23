# NEW-node-create-server — Server: aus einem Knoten ein Item oder ein Memo anlegen

## State

- Goal/Status: Geplant; Spec geschrieben, die Task ist für eine eigene Session vorbereitet.
- Next step: In eigener Session umsetzen: Plan aus `NEW-node-create-server_spec.md` ableiten, vorlegen und freigeben lassen.
- Open:
  - Nichts offen für die Umsetzung (2026-11-23)
- Decided:
  - Der Typ des Items wird nicht aus der Ebene abgeleitet; Mensch oder KI legt ihn je Knoten fest (Owner) (2026-11-23)
  - Ein Ideen-Knoten lässt sich auch zu einem Memo machen; ein Knoten mit nur einem Memo bleibt Idee, weil Memos nicht zählen (Owner) (2026-11-23)
  - Titel und Text des Knotens sind Standardwerte, Abschlusskriterien kommen immer vom Aufrufer, weil der Knoten keine hat (Zuschnitt) (2026-11-23)
- References: Spec `NEW-node-create-server_spec.md`; Story `STORY-103` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: NEW-area-remove-server

State confirmed after entry 2026-11-23 — Zuschnitt aus der Planung von STORY-103 (cd4bf940dad3)

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
