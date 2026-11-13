# NEW-mindmap — Mindmap: Themen-Gerippe zum Brainstormen und als Übersicht des Backlogs

## State

- Goal/Status: Geplant, noch nicht begonnen; Konzept steht in der Spec, Stories und Tasks sind angelegt.
- Next step: Aufbau der Mindmap-Seite mit dem Owner klären, dann mit der Story zum Gerüst beginnen.
- Open:
  - Genauer Aufbau der Mindmap-Seite (Auswahl der Maps, Schalter für Ansicht und Anordnung); der Owner will ihn noch klären (2026-11-13)
  - Ob das Feld Area neben der Mindmap bestehen bleibt (2026-11-13)
  - Von welchem Stand der neue Branch abzweigt und wann er zurückgeführt wird (2026-11-13)
- Decided:
  - Die Mindmap ist ein eigenes Datenmodell und nur ein Gerippe; sie verlinkt Items und Memos, ähnlich dem Feld Area, und kopiert nichts (2026-11-13)
  - Es gibt nur ein Modell: Ob ein Knoten bloße Idee oder schon im Backlog ist, ergibt sich aus dem, was daran hängt (2026-11-13)
  - Kernanforderung ist die Übersicht: mit wenigen Schritten sehen, was es gibt und was kommt; Items sind deshalb nie eigene Knoten (2026-11-13)
  - Topics der Memos bleiben unverändert und gehören nicht in die Mindmap (2026-11-13)
  - Der Viewer bekommt keine eigene LLM-Anbindung; die KI arbeitet über API und MCP (2026-11-13)
  - Die Umsetzung läuft in einem eigenen neuen Branch, weil es ein großer experimenteller Umbau ist, und in vielen kleinen Schritten (2026-11-13)
  - Der Markdown-Spiegel wird mitgeplant und ist für das Epic nicht Pflicht (2026-11-13)
- References: Spec `NEW-mindmap_spec.md`; Ideensammlung `NEW-mindmap-machbarkeit`; Stories `NEW-mm-geruest`, `NEW-mm-zuordnung`, `NEW-mm-ansichten`, `NEW-mm-freie-maps`, `NEW-mm-ueberfuehren`, `NEW-mm-ki`, `NEW-mm-spiegel`

State confirmed after entry 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung (7b9693bf6c7d)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `NEW-mindmap-machbarkeit`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.

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
