# EPIC-008 — Mindmap: Themen-Gerippe zum Brainstormen und als Übersicht des Backlogs

## State

- Goal/Status: Geplant; Konzept steht in der Spec, Stories und Tasks sind angelegt, Branch `todo_mindmap` ist der Ausgangspunkt der Umsetzung.
- Next step: Umsetzungsplan für `STORY-099` vorlegen und freigeben lassen; Stories zu Area-Ersatz und Markierungen mit dem Owner anlegen.
- Open:
  - Wie genau Area durch die Mindmap ersetzt wird (eigene Story, noch nicht angelegt) (2026-11-16)
- Decided:
  - Die Mindmap ist ein eigenes Datenmodell und nur ein Gerippe; sie verlinkt Items und Memos, ähnlich dem Feld Area, und kopiert nichts (2026-11-13)
  - Es gibt nur ein Modell: Ob ein Knoten bloße Idee oder schon im Backlog ist, ergibt sich aus dem, was daran hängt (2026-11-13)
  - Kernanforderung ist die Übersicht: mit wenigen Schritten sehen, was es gibt und was kommt; Items sind deshalb nie eigene Knoten (2026-11-13)
  - Topics der Memos bleiben unverändert und gehören nicht in die Mindmap (2026-11-13)
  - Der Viewer bekommt keine eigene LLM-Anbindung; die KI arbeitet über API und MCP (2026-11-13)
  - Die Umsetzung läuft in einem eigenen neuen Branch, weil es ein großer experimenteller Umbau ist, und in vielen kleinen Schritten (2026-11-13)
  - Der Markdown-Spiegel wird mitgeplant und ist für das Epic nicht Pflicht (2026-11-13)
  - Der Seitenaufbau folgt zunächst dem Backlog (Sidebar, Baum, Detailspalte); die Detailspalte ist schließbar; spätere Anpassung ist möglich (2026-11-16)
  - Die Mindmap ersetzt das Feld Area (2026-11-16)
  - Der Branch heißt `todo_mindmap`, zweigt von `main` ab und enthält die Planung per Merge aus `claude/nice-volta-6mvn99` (2026-11-16)
- References: Spec `EPIC-008_spec.md`; Ideensammlung `TASK-064`; Stories `STORY-099`, `STORY-100`, `STORY-101`, `STORY-102`, `STORY-103`, `STORY-104`, `STORY-105`

State confirmed after entry 2026-11-16 — Seitenaufbau, Area, Branch (d6499e99d67c)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `TASK-064`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.

### Decided

- Die Mindmap ist ein eigenes Datenmodell und nur ein Gerippe; sie verlinkt Items und Memos, ähnlich dem Feld Area, und kopiert nichts
- Es gibt nur ein Modell: Ob ein Knoten bloße Idee oder schon im Backlog ist, ergibt sich aus dem, was daran hängt
- Kernanforderung ist die Übersicht: mit wenigen Schritten sehen, was es gibt und was kommt; Items sind deshalb nie eigene Knoten
- Topics der Memos bleiben unverändert und gehören nicht in die Mindmap
- Der Viewer bekommt keine eigene LLM-Anbindung; die KI arbeitet über API und MCP
- Die Umsetzung läuft in einem eigenen neuen Branch, weil es ein großer experimenteller Umbau ist, und in vielen kleinen Schritten
- Der Markdown-Spiegel wird mitgeplant und ist für das Epic nicht Pflicht

### Open

- Genauer Aufbau der Mindmap-Seite (Auswahl der Maps, Schalter für Ansicht und Anordnung); der Owner will ihn noch klären
- Ob das Feld Area neben der Mindmap bestehen bleibt
- Von welchem Stand der neue Branch abzweigt und wann er zurückgeführt wird

## 2026-11-16 — Seitenaufbau, Area, Branch

### Discussed

- Seitenaufbau: A (Sidebar, Baum, Detailspalte wie im Backlog), B (Mindmap vorn, Detail schwebend), C (Reiter für Maps). A passt zum vorhandenen Seitengerüst (`STORY-088`) und ist am wenigsten Aufwand.
- Area: daneben lassen (doppelte Einordnung) oder ersetzen bzw. ableiten (sauberer, späterer Umbau).
- Branch: `main` enthielt die Planung von Epic 8 nicht; sie lag nur auf `claude/nice-volta-6mvn99`.

### Decided

- Seitenaufbau zunächst wie im Backlog (Variante A); die Detailspalte ist schließbar; spätere Anpassung ist möglich
- Die Mindmap ersetzt das Feld Area
- Branch `todo_mindmap`, von `main` abgezweigt, Planung per Merge hereingeholt; main ist danach in ihm enthalten und ist der Ausgangspunkt

### Open

- Open from 2026-11-13 (Aufbau der Mindmap-Seite, Area, Branch) resolved: siehe oben
- Wie Area ersetzt wird und wann (eigene Story, vom Owner freizugeben)
