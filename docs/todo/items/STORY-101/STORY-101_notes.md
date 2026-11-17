# STORY-101 — Mindmap-Ansichten: Fokus auf einen Knoten, Einzel- und Gesamtansicht, runde Anordnung, Abhängigkeiten

## State

- Goal/Status: Geplant; vier Tasks mit Spec und Notizen, Story-Spec steht; bereit zur Umsetzung in eigenen Sessions.
- Next step: `TASK-058` in eigener Session umsetzen (Plan aus der Spec, dem Owner vorlegen); danach `TASK-060`, `TASK-059`, `TASK-061`.
- Open:
  - Runde Anordnung bei großen Maps: ELK `radial`, `mrtree` oder eine eigene Berechnung; der Prototyp in `TASK-060` entscheidet (2026-11-13)
  - Seitenansicht „Nicht zugeordnet“ in der Gesamtansicht: Items des markierten Projekts oder aus; Vorschlag, vor `TASK-059` zu klären (2026-11-17)
- Decided:
  - Ein Anker ist nur eine Ansicht ab einem Knoten des einen Baums, mit Pfad zurück; so entstehen keine doppelten Orte (2026-11-13)
  - Am Item gibt es drei getrennte Aktionen: „Gehe hin“, „Erstelle“, „Anker“; kein Knoten entsteht still im Hintergrund (2026-11-13)
  - „Anker“ wird an einem Item erst angeboten, nachdem mit „Erstelle“ ein eigener Knoten angelegt wurde (2026-11-13)
  - Einzelansicht (eine Map) und Gesamtansicht mit gemeinsamer Wurzel, Projekte als erste Knoten, gefiltert über die Projektauswahl wie im Backlog (2026-11-13)
  - Verworfen: mehrere Maps nebeneinander, weil das vor allem rund unübersichtlich wird (2026-11-13)
  - Die Anordnung ist umschaltbar zwischen rund (Mitte mit Ästen ringsum) und Baum zur Seite (2026-11-13)
  - Abhängigkeiten werden nur zwischen Themen gezeigt (eine Linie, sobald ein Item aus A eines aus B braucht), an- und abschaltbar, standardmäßig aus (2026-11-13)
  - Der Fokus steht als `?focus=<uid>` in der Adresse (2026-11-17)
  - „Gehe hin“ blendet ein ausgeblendetes Projekt des Items ein und markiert es (2026-11-17)
  - Abhängigkeitslinien nur innerhalb eines Projekts, auch in der Gesamtansicht (2026-11-17)
  - Die Zusammenfassung der Linien liegt in der Server-Domain, weil dort der wirksame Knoten berechnet wird (2026-11-17)
  - Schalter für Ansicht, Anordnung und Abhängigkeiten sitzen als Sektionen der Seitenleiste (2026-11-17)
  - Reihenfolge der Tasks: `TASK-058`, `TASK-060`, `TASK-059`, `TASK-061`; je Task eigene Session und eigener Branch (2026-11-17)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Story-Spec `STORY-101_spec.md`; Tasks `TASK-058`, `TASK-059`, `TASK-060`, `TASK-061`; Ideensammlung `TASK-064`

State confirmed after entry 2026-11-17 — Planung der Umsetzung (f4da4047be14)

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

## 2026-11-17 — Planung der Umsetzung

### Discussed

- Befund im Code: Die Routen kennen keine Pfadparameter, ein Fokus in der Adresse braucht einen Query-Parameter. `BacklogItem` und sein Adapter liefern keine Abhängigkeiten; `TASK-061` braucht Server und Client. `getTree` arbeitet je Projekt, die Gesamtansicht lädt deshalb mehrere Bäume.
- „Gehe hin“ bei ausgeblendetem Projekt: einblenden und markieren (empfohlen) oder nur ein Hinweis.
- Abhängigkeitslinien über Projektgrenzen: nur innerhalb eines Projekts (empfohlen, weil `getTree` je Projekt arbeitet) oder auch dazwischen.
- Ort der Zusammenfassung: Server-Domain (empfohlen, dort liegt der wirksame Knoten) oder reine Funktion im Client.
- Ort der Schalter: Sektionen der Seitenleiste, wie `MapFilters` (Variante A des Epics).
- Reihenfolge: `TASK-058`, `TASK-060`, `TASK-059`, `TASK-061`; alle ändern `MindmapPage.tsx`, daher nacheinander.

### Decided

- Der Fokus steht als `?focus=<uid>` in der Adresse
- „Gehe hin“ blendet ein ausgeblendetes Projekt ein und markiert es
- Abhängigkeitslinien nur innerhalb eines Projekts, auch in der Gesamtansicht
- Die Zusammenfassung der Linien liegt in der Server-Domain
- Schalter für Ansicht, Anordnung und Abhängigkeiten sitzen als Sektionen der Seitenleiste
- Reihenfolge der Tasks: `TASK-058`, `TASK-060`, `TASK-059`, `TASK-061`; je Task eigene Session und eigener Branch

### Open

- Open from 2026-11-13 (Wo die Schalter sitzen) resolved: Sektionen der Seitenleiste, siehe oben
- Runde Anordnung bei großen Maps: der Prototyp in `TASK-060` entscheidet
- Seitenansicht „Nicht zugeordnet“ in der Gesamtansicht (Vorschlag: Items des markierten Projekts, sonst aus); vor `TASK-059` klären
