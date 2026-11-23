# TASK-078 — Systemtest Zuordnen und Vorschlagen; Prompt für Claude_Harness

## State

- Goal/Status: Geplant; Spec geschrieben, die Task ist für eine eigene Session vorbereitet.
- Next step: In eigener Session umsetzen: Plan aus `TASK-078_spec.md` ableiten, vorlegen und freigeben lassen.
- Open:
  - Nichts offen für die Umsetzung (2026-11-23)
- Decided:
  - Der Owner übergibt die Regel selbst; die KI liefert den Prompt (Owner) (2026-11-23)
  - Der Systemtest bildet das Gespräch durch getrennte Aufrufe nach, weil der Vorschlag keinen Zustand im Server hat (Zuschnitt) (2026-11-23)
- References: Spec `TASK-078_spec.md`; Story `STORY-104` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: TASK-077

State confirmed after entry 2026-11-23 — Zuschnitt aus der Planung von STORY-104 (b7578e67fba3)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-104

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-104 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-104_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Der Owner übergibt die Regel selbst; die KI liefert den Prompt (Owner)
- Der Systemtest bildet das Gespräch durch getrennte Aufrufe nach, weil der Vorschlag keinen Zustand im Server hat (Zuschnitt)

### Open

- Nichts.
