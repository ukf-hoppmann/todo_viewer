# TASK-059 — Mindmap: Gesamtansicht mit gemeinsamer Wurzel über die gewählten Projekte

## State

- Goal/Status: Spec vollständig, keine offene Frage; `TASK-058` ist erledigt, Plan wird erstellt (2026-11-18)
- Next step: Plan vom Owner freigeben lassen, dann umsetzen (2026-11-18)
- Open:
  - Keine
- Decided:
  - „Nicht zugeordnet“ zeigt in der Gesamtansicht die Items des markierten Projekts, sonst ist die Seitenansicht aus (2026-11-18)
  - Items ohne Knoten zählen in den Summen und im Zustand des Projektknotens nicht mit (2026-11-18)
  - Mehrere Projekte werden über einen RTK-Query-Endpunkt `getTrees` geladen (`queryFn`, parallel); der Server bleibt unverändert (2026-11-17)
  - Die gemeinsame Wurzel gehört keinem Projekt und nimmt nichts an (2026-11-17)
  - Keine Abhängigkeitslinien über Projektgrenzen (2026-11-17)
- References: Spec `TASK-059_spec.md`; Story-Spec `STORY-101_spec.md`

## 2026-11-18 — Planung: offene Fragen entschieden

### Discussed

- Seitenansicht „Nicht zugeordnet“ in der Gesamtansicht: markiertes Projekt (empfohlen), immer aus, oder alle gruppiert.
- Projektsumme mit oder ohne Items ohne Knoten.

### Decided

- Markiertes Projekt, sonst aus: das Ziel eines Drops liegt dann immer im selben Projekt. Verworfen: immer aus (nimmt die Zuordnung), alle gruppiert (Aufwand).
- Ohne Items ohne Knoten: sie sind kein Knoten und zählen auch in der Einzelansicht nicht im Baum; die Summe ist die der obersten Knoten, die ihre Unterknoten enthalten.

### Open

- Keine
