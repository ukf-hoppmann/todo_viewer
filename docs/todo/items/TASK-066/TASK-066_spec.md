# TASK-066 — Spec: Entfernte Platzierungen merken und wieder einsetzen

Gesamtbild: `STORY-102_spec.md`. Der Weg steht in `TASK-066_notes.md`. Setzt `TASK-063` voraus.

## Umfang

- „Hier entfernen“ löscht eine Platzierung nicht, sondern merkt sie als entfernt: Baum, Parent und Stelle bleiben
  gespeichert (eine Spalte an `mindmap_placements`, neue Migration).
- Abfragen, Summen und die Regel „höchstens einmal je Baum“ ignorieren entfernte Platzierungen.
- Ein Ast wird als Gruppe entfernt und kommt als Gruppe zurück (die entfernten Platzierungen seiner Unterknoten
  im selben Baum gehören dazu).
- „Wieder einsetzen“ gibt es über API, MCP und am Knoten („Früher in …“). Fehlt der alte Parent, ist der Platz
  belegt oder steht der Knoten im Baum inzwischen wieder, gilt die Ersatzregel (unter die Wurzel der Map) bzw. eine
  Ablehnung (Knoten steht schon wieder im Baum); die Oberfläche sagt es. Eine alte Stelle ist nie „belegt“: die
  Geschwister rücken nach.
- Die Regeln aus `TASK-063` gelten auch hier (Kreise, Projekt, Papierkorb).

## Nicht Teil

- Die Seitenansicht „Papierkorb“: `TASK-067`.
