# STORY-099 — Mindmap-Gerüst: Themenbaum je Projekt anlegen, ordnen und mit Notizen versehen

## State

- Goal/Status: Geplant; vier Tasks angelegt, Seitenaufbau entschieden.
- Next step: Umsetzungsplan vorlegen, dann `TASK-052` beginnen.
- Open:
  - Ob Ideen-Knoten eine Markierung bekommen („verworfen“, „später“): der Owner will mit Markierungen planen, Form und Story offen (2026-11-16)
- Decided:
  - Knoten sind leicht: Titel, optionaler Text, beliebige Tiefe; leere Knoten sind erlaubt (2026-11-13)
  - Je Projekt ein Baum mit dem Projekt als Wurzel (2026-11-13)
  - Die Lage eines Knotens wird von Anfang an als Platzierung (Knoten, Parent, Stelle) gespeichert, damit ein Ast später in mehreren Bäumen stehen kann (2026-11-13)
  - Platzierungen sind gleichberechtigt; es gibt kein Original mit Verweis (2026-11-13)
  - Umhängen innerhalb eines Baums ist immer möglich; Kreise werden verhindert (2026-11-13)
  - Knoten können Notizen bekommen, um Allgemeines zum Thema festzuhalten (2026-11-13)
  - Beim Öffnen sind zwei Ebenen offen, tiefere eingeklappt (2026-11-13)
  - Seitenaufbau wie im Backlog: Sidebar, Baum zur Seite, Detailspalte; die Detailspalte ist schließbar (2026-11-16)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`

State confirmed after entry 2026-11-16 — Seitenaufbau (9bc938ffcd86)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `TASK-064`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.
- Geplante Wiederverwendung: Ein Knoten wird ein Element des Workspace und bekommt so Verknüpfungen (`workspace_links`) und Papierkorb; die Notizen nutzen den gemeinsamen Baustein `DocumentsSection`; die Darstellung nutzt React Flow und ELK wie der Abhängigkeiten-Graph.

### Decided

- Knoten sind leicht: Titel, optionaler Text, beliebige Tiefe; leere Knoten sind erlaubt
- Je Projekt ein Baum mit dem Projekt als Wurzel
- Die Lage eines Knotens wird von Anfang an als Platzierung (Knoten, Parent, Stelle) gespeichert, damit ein Ast später in mehreren Bäumen stehen kann
- Platzierungen sind gleichberechtigt; es gibt kein Original mit Verweis
- Umhängen innerhalb eines Baums ist immer möglich; Kreise werden verhindert
- Knoten können Notizen bekommen, um Allgemeines zum Thema festzuhalten
- Beim Öffnen sind zwei Ebenen offen, tiefere eingeklappt

### Open

- Ob Ideen-Knoten eine eigene Markierung bekommen, etwa „verworfen“ oder „später“

## 2026-11-16 — Seitenaufbau

### Discussed

- Varianten A (wie Backlog), B (Mindmap vorn, Detail schwebend), C (Reiter für Maps); A nutzt das vorhandene Seitengerüst.
- Markierungen für Ideen-Knoten: „verworfen“ und „später“ blenden alte Ideen aus oder dimmen sie.

### Decided

- Seitenaufbau wie im Backlog, Detailspalte schließbar
- Markierungen werden mitgeplant

### Open

- Open from 2026-11-13 (Markierung für Ideen-Knoten) teilweise geklärt: wird geplant; Form und Story offen
