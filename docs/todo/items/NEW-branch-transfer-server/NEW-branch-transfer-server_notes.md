# NEW-branch-transfer-server — Server: einen Ast mit Vorschau ins Backlog überführen

## State

- Goal/Status: Geplant; Spec geschrieben, die Task ist für eine eigene Session vorbereitet.
- Next step: In eigener Session umsetzen: Plan aus `NEW-branch-transfer-server_spec.md` ableiten, vorlegen und freigeben lassen.
- Open:
  - Nichts offen für die Umsetzung (2026-11-23)
- Decided:
  - Kein Automatismus nach Ebene oder Tiefe; jeder Ast wird einzeln von Mensch oder KI entschieden; ein Knoten in Tiefe 5 kann ein eigenes Epic sein (Owner) (2026-11-23)
  - Die Backlog-Regeln werden nicht in der Mindmap nachgebaut; das Plugin backlog bekommt eine nicht schreibende Prüfung (Zuschnitt) (2026-11-23)
  - Kein Rückbau bei Teilfehlern; die Vorschau soll sie vorher abfangen (Zuschnitt) (2026-11-23)
- References: Spec `NEW-branch-transfer-server_spec.md`; Story `STORY-103` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: NEW-node-create-server

State confirmed after entry 2026-11-23 — Zuschnitt aus der Planung von STORY-103 (c4f4673d550b)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-103

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-103 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-103_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Kein Automatismus nach Ebene oder Tiefe; jeder Ast wird einzeln von Mensch oder KI entschieden; ein Knoten in Tiefe 5 kann ein eigenes Epic sein (Owner)
- Die Backlog-Regeln werden nicht in der Mindmap nachgebaut; das Plugin backlog bekommt eine nicht schreibende Prüfung (Zuschnitt)
- Kein Rückbau bei Teilfehlern; die Vorschau soll sie vorher abfangen (Zuschnitt)

### Open

- Nichts.
