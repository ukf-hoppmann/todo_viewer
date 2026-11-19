# NEW-papierkorb-ansicht — Mindmap: Papierkorb-Ansicht, Knoten per Ziehen reaktivieren

## State

- Goal/Status: Geplant; Entscheidungen aus der Besprechung von `STORY-102` übernommen, nicht Pflicht für die Story.
- Next step: Nach `TASK-063` beginnen; Plan beim Start vorstellen.
- Open:
  - Keine
- Decided:
  - Eigene Seitenansicht „Papierkorb“ mit den gelöschten Knoten des Projekts, ein- und ausschaltbar wie „Nicht zugeordnet“ (2026-11-19)
  - Ziehen eines Knotens an eine neue Stelle reaktiviert ihn dort (Backend: wiederherstellen und umziehen aus `TASK-063`) (2026-11-19)
  - Die neue Stelle ersetzt die alte Platzierung im aktuellen Baum, Platzierungen in anderen Bäumen kommen wie vorher zurück (2026-11-19)
- References: Spec `NEW-papierkorb-ansicht_spec.md`; Story-Spec `STORY-102_spec.md`; Vorgänger `TASK-063`

State confirmed after entry 2026-11-19 — Übernahme der Entscheidungen aus STORY-102 (047acd81f843)

## 2026-11-19 — Übernahme der Entscheidungen aus STORY-102

### Discussed

- Der Owner will gelöschte Knoten per Ziehen an eine andere Stelle setzen. Die Mindmap-Seite hat bisher keine Papierkorb-Ansicht; Wiederherstellen läuft über den Workspace. Die Ansicht ist neu und wird als eigener Task geführt, damit `TASK-063` nicht zu groß wird (Owner).

### Decided

- Eigener Task, abhängig von `TASK-063`; das Backend bleibt in `TASK-063`.
- Wohin ein Knoten mit mehreren früheren Platzierungen kommt: neue Stelle ersetzt die alte im aktuellen Baum, andere Bäume wie vorher (Owner).

### Open

- Keine
