# TASK-054 — Mindmap: Knoten per Ziehen umhängen und umordnen

## State

- Goal/Status: Umsetzung vorgeplant; noch nicht begonnen, weil `TASK-052` und `TASK-053` offen sind und es das Plugin `mindmap` noch nicht gibt.
- Next step: Der Owner entscheidet die drei offenen Punkte; danach Spec schreiben. Umsetzung erst nach `TASK-053`.
- Open:
  - Technik des Ziehens: HTML5-Drag-and-drop am Knoten (Vorschlag) oder das Verschieben von React Flow (2026-11-16)
  - Ablegezonen am Zielknoten: oberes Viertel davor, unteres Viertel danach, Mitte darunter, wie im Baum (Vorschlag) (2026-11-16)
  - Ablegen auf einen eingeklappten Knoten klappt ihn auf (Vorschlag) (2026-11-16)
- Decided:
- References: Notizen `STORY-099`; Konzept `EPIC-008_spec.md`; Vorbilder `client/src/shared/tree/treeModel.ts` (`dropPosition`, `isInSubtree`), `client/src/plugins/backlog/model.ts` (`placementOf`)

State confirmed after entry 2026-11-16 — Vorplanung der Umsetzung (365d5f41ec25)

## 2026-11-16 — Vorplanung der Umsetzung

### Discussed

- Stand: `TASK-052` (Server) und `TASK-053` (Seite) sind offen; im Code gibt es noch kein Plugin `mindmap`. Der Plan stützt sich deshalb auf Annahmen über deren Ergebnis: eine Operation zum Umhängen mit Knoten, neuem Parent, Stelle und Versions-Token; Ablehnungen als `{code, message, details}`; ein Ereignis nach dem Umhängen, auf das die Seite neu lädt.
- Technik des Ziehens. Option A, HTML5-Drag-and-drop am Knoten (`draggable`, `dragover`, `drop`, im Knoten als `nodrag` markiert): gleiches Muster wie `TreeView`, in jsdom mit `fireEvent` prüfbar, braucht keine gemessenen Knotengrößen; Nachteil: beim Ziehen folgt nur das Geisterbild des Browsers, nicht der Knoten selbst. Option B, Verschieben von React Flow (`onNodeDrag`, `onNodeDragStop`, `getIntersectingNodes`): der Knoten folgt dem Zeiger; Nachteile: in jsdom kaum prüfbar (d3-drag, keine Maße), der Knoten muss nach jedem Ziehen in die berechnete Lage zurückspringen, und das Ziehen eines Knotens streitet mit dem Verschieben der Fläche. Empfehlung: A.
- Ablegezonen. Die Anordnung zur Seite stellt Geschwister untereinander; damit passt die Regel des Baums (`dropPosition`: oberes Viertel davor, unteres Viertel danach, Mitte darunter). Die Wurzel (Projekt) lässt sich nicht ziehen und nimmt nur „darunter“ an.
- Was nicht angeboten wird: der Knoten selbst, sein eigener Ast, „davor/danach“ an der Wurzel und eine Stelle, die nichts ändert. Die Regel ist eine reine Funktion in `domain/` des Plugins, nach dem Vorbild `placementOf`.
- Meldung: Lehnt der Server ab (etwa `version_conflict` oder Kreis), steht die übersetzte Meldung zum `code` in einer Leiste über der Map; sie lässt sich schließen und verschwindet beim nächsten erfolgreichen Umhängen.
- Eingeklapptes Ziel: Beim Ablegen „darunter“ wird der Ast ans Ende gehängt; Vorschlag, das Ziel dabei aufzuklappen, damit das Ergebnis sichtbar ist.
- Keine neue Abhängigkeit im Client nötig.

### Decided

- Noch nichts; die Vorschläge warten auf den Owner.

### Open

- Technik des Ziehens: HTML5-Drag-and-drop am Knoten (Vorschlag) oder das Verschieben von React Flow
- Ablegezonen am Zielknoten wie im Baum (Vorschlag)
- Ablegen auf einen eingeklappten Knoten klappt ihn auf (Vorschlag)
