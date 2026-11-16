# TASK-054 — Mindmap: Knoten per Ziehen umhängen und umordnen

## State

- Goal/Status: Umgesetzt und geprüft (Typen, Client-Tests 1240 grün); wartet auf Bestätigung des Owners. Im Browser nicht ausprobiert (2026-11-16)
- Next step: Der Owner bestätigt oder verlangt Änderungen; danach `TASK-055`.
- Open:
  - Lint meldet 5 Fehler in `core/ui-state/usePersistentState.ts`; sie bestanden vorher und gehören nicht zu diesem Task (2026-11-16)
  - Der Ablauf ist noch nicht im Browser geprüft, weil die Sitzung keinen laufenden Viewer hatte (2026-11-16)
- Decided:
  - Ziehen per HTML5-Drag-and-drop am Knoten (2026-11-16)
  - Ablegezonen wie im Baum: oberes Viertel davor, unteres Viertel danach, Mitte darunter (2026-11-16)
  - Ein eingeklapptes Ziel klappt beim Ablegen „darunter“ auf (2026-11-16)
  - Die Regel liegt als reine Funktion `dropPlacement` in `domain/tree.ts`; der Server prüft trotzdem selbst, seine Ablehnung steht über der Map (2026-11-16)
- References: Notizen `STORY-099`; Konzept `EPIC-008_spec.md`; Doku `docs/techdocs/neubau-client.md` (Abschnitt „Plugin `mindmap`“)

State confirmed after entry 2026-11-16 — Entscheidungen und Umsetzung (e950f7cfeff1)

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

## 2026-11-16 — Stand nach TASK-053 geprüft

### Discussed

- `origin/todo_mindmap` (mit `TASK-052` und `TASK-053`) ist in den Arbeitsbranch gemergt, ohne Konflikte.
- Server: `move_node` (POST `/api/mindmap/nodes/{ref}/move` mit `version`, `parent` (leer: unter die Wurzel), `position`) gibt es. Die Stelle zählt unter den lebenden Geschwistern ohne den gezogenen Knoten, wie bei `placementOf`. Ablehnungen kommen mit `code`, etwa `mindmap_loop`.
- Client: Dem Plugin fehlt nur die Mutation fürs Umhängen in `api.ts`. Die Seite hat schon die Fehlerleiste über der Map (`mindmap.error`), sie zeigt die Meldung des Servers; `tree.ts` in `domain/` nimmt die Regel fürs Ablegen auf; die Aktionen der Knoten laufen über `MapActions`. Die Knoten sind in React Flow als nicht ziehbar gesetzt, was zu HTML5-Drag-and-drop passt.
- Die Seite passt ihren Ausschnitt nach jeder Änderung der Struktur neu ein; das gilt dann auch nach dem Umhängen.

### Open

- Unverändert die drei Punkte vom 2026-11-16 (Technik des Ziehens, Ablegezonen, eingeklapptes Ziel)

## 2026-11-16 — Entscheidungen und Umsetzung

### Discussed

- Der Owner hat die drei Vorschläge angenommen: HTML5-Drag-and-drop, Zonen wie im Baum, eingeklapptes Ziel aufklappen.
- Umgesetzt mit Test zuerst für die Regel (`dropPlacement`, 6 Fälle), dann die Mutation `moveNode`, das Ziehen im Knoten und die Verdrahtung in der Seite. Die Stelle zählt wie im Server ohne den gezogenen Knoten.
- Die Fake-Datenbank der Tests (`fakeMindmapBackend`) kennt jetzt das Umhängen und nummeriert die Geschwister neu.
- Geprüft: `tsc -b` ohne Fehler; alle Client-Tests grün (109 Dateien, 1240 Tests), darunter 7 neue Seitentests und 6 neue Regeltests; Lint ohne Befund in den geänderten Dateien. Nicht geprüft: Ablauf im Browser mit echtem Zeiger.

### Decided

- Siehe Kopf: die drei Vorschläge sind angenommen.

### Open from 2026-11-16 (Vorplanung) resolved: Technik des Ziehens, Ablegezonen und eingeklapptes Ziel sind entschieden.

### Open

- Ablauf im Browser prüfen
