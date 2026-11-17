# TASK-059 — Mindmap: Gesamtansicht mit gemeinsamer Wurzel über die gewählten Projekte

## State

- Goal/Status: Spec steht; wartet auf `TASK-058`.
- Next step: Nach dem Merge von `TASK-058` Plan aus der Spec erstellen und umsetzen.
- Open:
  - In der Gesamtansicht zeigt die Seitenansicht „Nicht zugeordnet“ die Items des markierten Projekts, sonst ist sie aus; das ist ein Vorschlag, noch nicht vom Owner bestätigt (2026-11-17)
- Decided:
  - Mehrere Projekte werden über einen RTK-Query-Endpunkt `getTrees` geladen (`queryFn`, parallel); der Server bleibt unverändert (2026-11-17)
  - Die gemeinsame Wurzel gehört keinem Projekt und nimmt nichts an (2026-11-17)
  - Keine Abhängigkeitslinien über Projektgrenzen (2026-11-17)
- References: Spec `TASK-059_spec.md`; Story-Spec `STORY-101_spec.md`

State confirmed after entry 2026-11-17 — Anlage aus der Planung der Story (3af5b3960e5e)

## 2026-11-17 — Anlage aus der Planung der Story

### Discussed

- Planung der Story `STORY-101` mit dem Owner.

### Decided

- Ein Endpunkt `getTrees` statt Hooks in Schleifen; der Server bleibt unverändert
- Gemeinsame Wurzel ohne Anlegen, Umhängen, Zuordnen

### Open

- In der Gesamtansicht zeigt die Seitenansicht „Nicht zugeordnet“ die Items des markierten Projekts, sonst ist sie aus; das ist ein Vorschlag, noch nicht vom Owner bestätigt
