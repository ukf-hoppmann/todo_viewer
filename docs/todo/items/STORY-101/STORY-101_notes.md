# STORY-101 — Mindmap-Ansichten: Fokus auf einen Knoten, Einzel- und Gesamtansicht, runde Anordnung, Abhängigkeiten

## State

- Goal/Status: Geplant; vier Tasks angelegt.
- Next step: Vor Beginn den Aufbau der Mindmap-Seite mit dem Owner klären.
- Open:
  - Runde Anordnung bei großen Maps: ELK `radial` oder eine eigene Anordnung; ein Prototyp soll es zeigen (2026-11-13)
  - Wo die Schalter für Ansicht und Anordnung sitzen, hängt am Aufbau der Mindmap-Seite (2026-11-13)
- Decided:
  - Ein Anker ist nur eine Ansicht ab einem Knoten des einen Baums, mit Pfad zurück; so entstehen keine doppelten Orte (2026-11-13)
  - Am Item gibt es drei getrennte Aktionen: „Gehe hin“, „Erstelle“, „Anker“; kein Knoten entsteht still im Hintergrund (2026-11-13)
  - „Anker“ wird an einem Item erst angeboten, nachdem mit „Erstelle“ ein eigener Knoten angelegt wurde (2026-11-13)
  - Einzelansicht (eine Map) und Gesamtansicht mit gemeinsamer Wurzel, Projekte als erste Knoten, gefiltert über die Projektauswahl wie im Backlog (2026-11-13)
  - Verworfen: mehrere Maps nebeneinander, weil das vor allem rund unübersichtlich wird (2026-11-13)
  - Die Anordnung ist umschaltbar zwischen rund (Mitte mit Ästen ringsum) und Baum zur Seite (2026-11-13)
  - Abhängigkeiten werden nur zwischen Themen gezeigt (eine Linie, sobald ein Item aus A eines aus B braucht), an- und abschaltbar, standardmäßig aus (2026-11-13)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`

State confirmed after entry 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung (eb5c7a59da10)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `TASK-064`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.
- Vergleich: Workflowy und Dynalist öffnen jeden Punkt als Wurzel (Fokus); XMind, MindManager und Freeplane kennen Fokus und ausgelagerte Teil-Maps.

### Decided

- Ein Anker ist nur eine Ansicht ab einem Knoten des einen Baums, mit Pfad zurück; so entstehen keine doppelten Orte
- Am Item gibt es drei getrennte Aktionen: „Gehe hin“, „Erstelle“, „Anker“; kein Knoten entsteht still im Hintergrund
- „Anker“ wird an einem Item erst angeboten, nachdem mit „Erstelle“ ein eigener Knoten angelegt wurde
- Einzelansicht (eine Map) und Gesamtansicht mit gemeinsamer Wurzel, Projekte als erste Knoten, gefiltert über die Projektauswahl wie im Backlog
- Verworfen: mehrere Maps nebeneinander, weil das vor allem rund unübersichtlich wird
- Die Anordnung ist umschaltbar zwischen rund (Mitte mit Ästen ringsum) und Baum zur Seite
- Abhängigkeiten werden nur zwischen Themen gezeigt (eine Linie, sobald ein Item aus A eines aus B braucht), an- und abschaltbar, standardmäßig aus

### Open

- Runde Anordnung bei großen Maps: ELK `radial` oder eine eigene Anordnung; ein Prototyp soll es zeigen
- Wo die Schalter für Ansicht und Anordnung sitzen, hängt am Aufbau der Mindmap-Seite
