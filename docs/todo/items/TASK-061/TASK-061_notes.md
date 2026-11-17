# TASK-061 — Mindmap: Abhängigkeiten zwischen Themen ein- und ausblenden

## State

- Goal/Status: Spec steht; berührt Server und Client.
- Next step: Plan aus der Spec erstellen: Server (Port, Domain, `TreeOut.links`, Schema), dann Client (`liftLinks`, Darstellung, Schalter), Integration.
- Open:
- Decided:
  - Die Zusammenfassung der Linien liegt in der Server-Domain, weil dort der wirksame Knoten berechnet wird (2026-11-17)
  - Nur Abhängigkeiten innerhalb eines Projekts; auch in der Gesamtansicht keine Linien zwischen Projekten (2026-11-17)
  - `BacklogItem` liefert bisher keine `dependencies`; Port und Adapter werden erweitert (2026-11-17)
- References: Spec `TASK-061_spec.md`; Story-Spec `STORY-101_spec.md`

State confirmed after entry 2026-11-17 — Anlage aus der Planung der Story (3f69281cdb6e)

## 2026-11-17 — Anlage aus der Planung der Story

### Discussed

- Planung der Story `STORY-101` mit dem Owner; Entscheidungen 2 und 3 der Planung betreffen diesen Task.
- Beim Lesen des Codes fiel auf: `BacklogItem` (`application/ports.py`) und der Adapter liefern keine Abhängigkeiten, der Task ist größer als das Ticket vermuten lässt.

### Decided

- Zusammenfassung in der Server-Domain
- Nur innerhalb eines Projekts

### Open

- Nichts offen.
