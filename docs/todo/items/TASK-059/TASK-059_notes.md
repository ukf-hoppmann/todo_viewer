# TASK-059 — Mindmap: Gesamtansicht mit gemeinsamer Wurzel über die gewählten Projekte

## State

- Goal/Status: umgesetzt (ff3d8dc5), `Awaiting confirmation`; alle Client-Tests und `tsc` grün (2026-11-18)
- Next step: Owner bestätigt oder nennt Fehlendes (2026-11-18)
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

## 2026-11-18 — Umsetzung

### Discussed

- Plan mit Owner abgestimmt und freigegeben; umgesetzt in fünf Abschnitten (Domain, `getTrees`, Umschalter, Seite, Doku).

### Decided

- `combinedTree` bekommt eine Fabrik für den Projektknoten, damit `domain/tree.ts` keine API-Typen importiert.
- Ein Drop gilt nur im selben Projekt: Quelle und Ziel werden gegen die Knoten des Zielprojekts (wie vom Server geliefert) geprüft.

### Open

- Keine
