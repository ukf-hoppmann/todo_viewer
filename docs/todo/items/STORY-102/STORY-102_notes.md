# STORY-102 — Freie Maps und Äste zwischen Bäumen umhängen und übertragen

## State

- Goal/Status: Geplant; zwei Tasks angelegt.
- Next step: Nach Gerüst und Zuordnung mit dem Task zu den freien Maps beginnen.
- Open:
  - Besprechung in Arbeit, Themenplan 2026-11-18: 1 Auswahl der Maps, 2 Memo-Map, 3 Löschen freier Maps, 4 Bedienung Umhängen/Übertragen, 5 Markierung und Pfad im Fokus, 6 „Hier entfernen“ und „Knoten löschen“, 7 Summen und Zustand, 8 verbotene Fälle, 9 Markdown-Spiegel (2026-11-18)
  - Wo man zwischen Projektbaum und freien Maps wählt, hängt am Aufbau der Mindmap-Seite; Thema 1 (2026-11-13)
- Decided:
  - Projektbaum und freie Maps werden gemischt, damit man flexibel gestalten kann (2026-11-13)
  - Freie Maps gehören zu einem Projekt; Übergreifendes kommt ins eingebaute Projekt „Allgemein“ (2026-11-13)
  - Die Mindmap zu einem Memo lebt allein in diesem Memo (2026-11-13)
  - Nichts wird kopiert; es gibt „umhängen“ (aus A weg, in B drin) und „übertragen“ (derselbe Ast in A und B) (2026-11-13)
  - Übertragen geht nur zwischen Bäumen; innerhalb eines Baums gibt es nur Umhängen (2026-11-13)
  - Platzierungen sind gleichberechtigt: Wird der Ast aus einem Baum entfernt, bleibt er im anderen vollwertig (2026-11-13)
  - Verworfen: Verweis-Knoten auf ein Original, weil der Verweis ins Leere zeigt, sobald das Original entfernt wird (2026-11-13)
  - Ein übertragener Ast ist ein gemeinsamer Knoten und überall gleich; ein „Trennen“ in eine eigenständige Kopie gibt es vorerst nicht, bei Bedarf wird umgebaut (2026-11-13)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`

State confirmed after entry 2026-11-18 — Themenplan der Besprechung (cb09d2d9e268)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `TASK-064`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.
- Folgen des Übertragens: Summen ohne Doppelzählung, zwei Aktionen zum Entfernen, im Fokus folgt der Pfad dem Weg, über den man kam, übertragene Äste sind markiert.

### Decided

- Projektbaum und freie Maps werden gemischt, damit man flexibel gestalten kann
- Freie Maps gehören zu einem Projekt; Übergreifendes kommt ins eingebaute Projekt „Allgemein“
- Die Mindmap zu einem Memo lebt allein in diesem Memo
- Nichts wird kopiert; es gibt „umhängen“ (aus A weg, in B drin) und „übertragen“ (derselbe Ast in A und B)
- Übertragen geht nur zwischen Bäumen; innerhalb eines Baums gibt es nur Umhängen
- Platzierungen sind gleichberechtigt: Wird der Ast aus einem Baum entfernt, bleibt er im anderen vollwertig
- Verworfen: Verweis-Knoten auf ein Original, weil der Verweis ins Leere zeigt, sobald das Original entfernt wird

### Open

- Der Owner erwartet, dass sich übertragene Äste in beiden Bäumen unterschiedlich entwickeln können. Mit einem gemeinsamen Knoten ist der Ast aber überall derselbe; getrennte Entwicklung hieße trennen, also doch kopieren. Rückfrage gestellt
- Wo man zwischen Projektbaum und freien Maps wählt, hängt am Aufbau der Mindmap-Seite

## 2026-11-13 — Übertragene Äste bleiben gemeinsam

### Discussed

- Open vom 2026-11-13 (getrennte Entwicklung übertragener Äste) geklärt. Zur Wahl standen: gemeinsam (ein Ast, überall gleich) oder zusätzlich eine Aktion „trennen“, die eine eigenständige Kopie erzeugt.

### Decided

- Start mit „gemeinsam“; wenn sich zeigt, dass getrennte Entwicklung gebraucht wird, wird umgebaut (Owner).

### Open

- Wo man zwischen Projektbaum und freien Maps wählt, hängt weiter am Aufbau der Mindmap-Seite.

## 2026-11-18 — Themenplan der Besprechung

### Discussed

- Vor der Umsetzung von `TASK-062` und `TASK-063` werden offene Punkte der Reihe nach geklärt. Die Abhängigkeiten `STORY-099` und `STORY-100` sind abgeschlossen; `STORY-101` wartet auf Bestätigung.
- Themen: 1 Auswahl zwischen Projektbaum und freien Maps (blockiert `TASK-062`), 2 Map eines Memos, 3 Löschen freier Maps, 4 Bedienung von Umhängen und Übertragen, 5 Markierung übertragener Äste und Pfad im Fokus, 6 „Hier entfernen“ und „Knoten löschen“, 7 Summen und Zustand bei übertragenen Ästen, 8 verbotene Fälle (Kreise, Knoten schon im Zielbaum), 9 Folgen für den Markdown-Spiegel `STORY-105`.

### Open

- Alle neun Themen; Reihenfolge wie oben.
