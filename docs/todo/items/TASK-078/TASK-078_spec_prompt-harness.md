# TASK-078 — Prompt für Claude_Harness: neue Backlog-Items dem Themenbaum zuordnen

Zu `STORY-104`. Diesen Text gibt der Owner selbst in einer Sitzung im Repository von Claude_Harness ein. Die KI im
ToDo-Viewer übergibt nichts an Claude_Harness.

---

## Prompt

Ziel: Der Skill `todo` soll eine Regel bekommen. Wer im API-Modus ein Backlog-Item anlegt, ordnet es dem Themenbaum
(der Mindmap) des ToDo-Viewers zu. Neue Knoten legt die KI nur nach ausdrücklicher Zustimmung des Owners an.

Hintergrund: Der ToDo-Viewer (Projekt `todo_viewer`) hat eine Mindmap je Projekt. Ihre Knoten sind Themen; Items hängen
an Knoten. Items ohne Knoten stehen in der Ansicht „Nicht zugeordnet“. Die Regel steht dort bereits in den
Beschreibungen der MCP-Tools; die KI dort sieht sie also schon. Sie soll zusätzlich in den Skill, damit auch Sitzungen
sie kennen, die den Viewer über `backlog_api.py` bedienen.

Die Regel (Wortlaut der Tool-Beschreibungen, an die Sprache des Skills anpassen):

> Regel beim Anlegen eines Items: Lies zuerst den Themenbaum (mindmap_get_tree). Passt ein Knoten, lege das Item dort
> an (mindmap_create_item_at_node) oder ordne ein vorhandenes zu (mindmap_assign_item). Passt keiner, schlage dem Owner
> im Gespräch einen Knoten oder Unterknoten vor (Titel, Ort im Baum) und lege ihn (mindmap_create_node) erst nach
> seiner Zustimmung an; erfinde keine Themen. Ohne Zustimmung lege das Item ohne Knoten an (backlog_create_item); es
> steht dann unter „Nicht zugeordnet“.

Die Werkzeuge (Namen, wie der Viewer sie unter `/mcp` mit `tools/list` ausgibt; HTTP-Pfade unter `/api/mindmap/…`):

| Werkzeug | Zweck | Wichtige Eingaben |
|---|---|---|
| `mindmap_get_tree` | Themenbaum lesen: Knoten (uid, Titel, Parent, Stelle, Zahlen, Zustand) und die Items ohne Knoten (`unassigned`) | `project` |
| `mindmap_create_item_at_node` | Item anlegen und an den Knoten hängen | `node`, `type` (Epic, Story, Task), `fields` (`completion_criteria` Pflicht; `title`, `goal` sonst vom Knoten) |
| `mindmap_assign_item` | vorhandenes Item an einen Knoten hängen | `node`, `item`, `replace` (nur um einen anderen Knoten zu ersetzen) |
| `mindmap_create_node` | Knoten anlegen, nur nach Zustimmung des Owners | `project`, `title`, `text`, `parent` |
| `backlog_create_item` | Item ohne Knoten anlegen, wenn keiner passt oder der Owner ablehnt | `project`, `type`, `fields` |

Der Vorschlag eines Knotens ist kein Zustand im Server: Die KI fragt im Gespräch, und erst nach dem „Ja“ des Owners
ruft sie `mindmap_create_node` auf. Ohne Antwort oder bei „Nein“ entsteht kein Knoten.

Wohin: Skill `todo`, Abschnitt „Working rules“, im Bereich zu neuen Items (neben „New work goes under an existing epic
or story …“). Der Wortlaut muss zur Sprache und zum Stil des Skills passen. Erwähne die Regel nur für den API-Modus.

Nicht Teil dieses Auftrags: der Dateimodus (Cloud-Sitzungen ohne Server). Dort gibt es keinen Themenbaum, bis der
Mindmap-Spiegel (`STORY-105` im Backlog des ToDo-Viewers) ihn als Dateien liefert; die Regel dafür folgt dann. Bitte die
Regel jetzt nur für den API-Modus aufnehmen und im Skill vermerken, dass der Dateimodus noch offen ist.

Vorgehen: Lege dafür ein Backlog-Item in Claude_Harness an (nach den dortigen Regeln), setze die Regel um und prüfe, dass
Skill-Text und Tool-Namen übereinstimmen.
