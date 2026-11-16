# TASK-052 — Mindmap-Server: Knoten, Platzierungen und Projektbaum mit API und MCP

## State

- Goal/Status: Abgeschlossen: vom Owner bestätigt (2026-11-16), nach `todo_mindmap` gemergt.
- Next step: `TASK-053` (Mindmap-Seite) startet in einer neuen Session.
- Open:
  - Wie ein Kind behandelt wird, das in mehreren Bäumen steht, wenn der Parent gelöscht wird: erst mit `STORY-102` zu klären (2026-11-16)
- Decided:
  - Plugin `mindmap` mit Elementtyp `mindmap_node` (Label `NODE`), Tabellen mit Präfix `mindmap_`: Bäume, Knoten, Platzierungen (2026-11-16)
  - Kein Parent-Feld am Knoten; die Lage steht nur in `mindmap_placements` (Baum, Knoten, Parent, Stelle) (2026-11-16)
  - Der Projektbaum entsteht beim ersten Knoten; Baumart als Nachschlagetabelle, damit freie Maps ohne Umbau folgen können (2026-11-16)
  - Ein Ast geht mit all seinen Kindern zusammen in den Papierkorb und kommt mit ihnen zurück; ein Knoten kommt nicht zurück, solange sein Parent im Papierkorb liegt (2026-11-16)
  - Stellen: Gelöschte Geschwister behalten ihre Stelle, Leser sehen lückenlose Stellen unter den sichtbaren Geschwistern (2026-11-16)
  - Papierkorb und Wiederherstellen über die Operationen von `workspace` statt eigener Operationen; mit der Bestätigung des Tasks vom Owner angenommen (2026-11-16)
  - Ereignis `mindmap.node.changed` mit `created`, `updated`, `moved`, `deleted`, `restored` (2026-11-16)
- References: Story `STORY-099`, Epic `EPIC-008` mit Spec `EPIC-008_spec.md`; Schnittstelle `docs/techdocs/neubau-server.md` (Abschnitt „Plugin `mindmap`“); Tests unter `tests/implementation/{unit,integration}/server/plugins/mindmap/`

State confirmed after entry 2026-11-16 — Bestätigung und Merge (5083f0877576)

## 2026-11-16 — Umsetzung und Entscheidungen

### Discussed

- Vorbilder: Plugin `alarms` (Aufbau, Schichten, `plugin.py`), `topic_loop` in `plugins/memos/domain/topics.py` (Kreisprüfung), Papierkorb von `workspace` (`children`, `restore_guard`, `purger`).
- Wie ein Ast mit Kindern im Papierkorb behandelt wird. Optionen: (a) nur der Knoten, Kinder rücken zum Parent des Gelöschten; (b) der ganze Ast zusammen; (c) Löschen nur ohne Kinder. Empfehlung und Entscheidung des Plans (Auftrag an die Session): (b). Gründe: ein Knoten ist ein Thema mit seinen Unterthemen, (a) würde die Struktur unbemerkt umbauen, (c) zwingt zu vielen Schritten. Das passt zu `children` des Papierkorbs von `workspace` (Backlog verfährt bei Items so); ohne `cascade` meldet `workspace_delete_element` `has_children` und löscht nichts.
- Wiederherstellen: `workspace` holt die Wurzel des Astes mit allen Kindern zurück, die zur selben Zeit gelöscht wurden; ein früher einzeln gelöschtes Kind bleibt draußen. Ein Kind allein kommt nicht zurück, solange sein Parent im Papierkorb liegt (`mindmap_parent_in_trash`), damit kein verwaister Knoten entsteht.
- Papierkorb-Operationen: Der Auftrag nennt „in den Papierkorb legen, wiederherstellen“ als Operationen. Alle anderen Plugins (`backlog`, `memos`, `alarms`) bieten das nicht selbst an, sondern nutzen `workspace_delete_element` und `workspace_restore_elements`; eigene Operationen bräuchten Zugriff auf den Papierkorb-Dienst, der nicht zur öffentlichen Schnittstelle von `workspace` gehört (nur `TrashRegistry`). Umsetzung deshalb wie bei den anderen Plugins; `mindmap` meldet dazu `mindmap.node.changed` (`deleted`, `restored`) aus dem Ereignis `workspace.element.changed`.
- Stellen unter Geschwistern: Positionen werden gespeichert; ein Knoten im Papierkorb behält seine Stelle, damit er beim Wiederherstellen zurückkehrt, gleiche Stellen ordnet der Knoten. Lesen liefert lückenlose Stellen unter den sichtbaren Geschwistern.
- Unbekanntes Projekt beim Lesen eines noch leeren Baums: `get_tree` legt nichts an; `tree_uid` ist dann leer.

### Decided

- Siehe Kopf; ein Ast wandert zusammen in den Papierkorb und zurück.
- Papierkorb und Wiederherstellen über `workspace_*` (wie bei den anderen Plugins), mit Ereignissen von `mindmap`.

### Open

- (erledigt mit der Bestätigung) Ob der Owner eigene Operationen `mindmap_delete_node` und `mindmap_restore_node` will (dann wäre eine kleine Erweiterung der öffentlichen Schnittstelle von `workspace` nötig, die den Papierkorb-Dienst für Plugins freigibt).
- Kind in mehreren Bäumen beim Löschen des Parents (`STORY-102`).

## 2026-11-16 — Bestätigung und Merge

### Decided

- Der Owner bestätigt `TASK-052` als `Completed`; der Branch `claude/task-052-mindmap-server` ist nach `todo_mindmap` gemergt. Damit gilt die Lösung ohne eigene Papierkorb-Operationen.
