# `STORY-074` — Abhängigkeiten-Graph

Grundlage: `EPIC-007_spec.md`, Abschnitt 9. Verhalten wie im README des alten Viewers, Abschnitt
„Views → Abhängigkeiten“.

## Umfang

- Domäne: Graph aus `backlog_dependencies` (reine Funktion, Vorlage
  `web/src/domain`), Komponenten-Erkennung, linke Spalte für Knoten ohne
  Abhängigkeiten.
- Ansicht mit `@xyflow/react` und `elkjs`, per Lazy-Import geladen; Knoten
  mit Fortschrittsring.
- Filter der Seitenleiste wie im Baum.

## Tests

Domäne zuerst; UI-Test für Hervorheben und Mehrfachauswahl.
