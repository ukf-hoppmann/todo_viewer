# NEW-mirror-format — Mindmap-Spiegel: Dateiformat und Codec mit Golden-Files

## State

- Goal/Status: Geplant; Spec geschrieben, die Task ist für eine eigene Session vorbereitet.
- Next step: In eigener Session umsetzen: Plan aus `NEW-mirror-format_spec.md` ableiten, vorlegen und freigeben lassen.
- Open:
  - Nichts offen für die Umsetzung (2026-11-23)
- Decided:
  - Der Inhalt eines Knotens steht einmal in einer Datei; jeder Baum ist eine Datei mit Verweisen; mehrfache Platzierungen sind Verweise (Owner) (2026-11-23)
  - Dateiname je Knoten `NODE-nnn.md`, Bäume `project.md` und `maps/<name>.md`; Identität ist die Uid, nicht der Dateiname (Zuschnitt) (2026-11-23)
  - Das Format hat eine eigene Versionszählung (Version 1), unabhängig vom Backlog-Format (Zuschnitt) (2026-11-23)
- References: Spec `NEW-mirror-format_spec.md`; Story `STORY-105` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: keine

State confirmed after entry 2026-11-23 — Zuschnitt aus der Planung von STORY-105 (09d6beb3e01c)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-105

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-105 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-105_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Der Inhalt eines Knotens steht einmal in einer Datei; jeder Baum ist eine Datei mit Verweisen; mehrfache Platzierungen sind Verweise (Owner)
- Dateiname je Knoten `NODE-nnn.md`, Bäume `project.md` und `maps/<name>.md`; Identität ist die Uid, nicht der Dateiname (Zuschnitt)
- Das Format hat eine eigene Versionszählung (Version 1), unabhängig vom Backlog-Format (Zuschnitt)

### Open

- Nichts.
