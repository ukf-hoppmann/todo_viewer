# TASK-072 — Prompt 1: Themenbaum aus den Items erzeugen

Der Text zwischen den Linien ist ein einziger Prompt. Der Owner kopiert ihn in eine Claude-Code-Sitzung im Checkout
des Projekts, dessen Viewer-Server läuft und als MCP-Server `todo-viewer` (Pfad `/mcp`) eingebunden ist. Die
Werkzeugnamen sind gegen `tools/list` des Servers (Stand nach `TASK-071`) geprüft.

Erprobt am 2026-11-24 gegen einen echten Server mit einem Beispielprojekt (20 Items, kein Knoten): siehe
`TASK-072_notes.md`.

---

Du baust für ein Projekt im ToDo-Viewer einen Themenbaum (Mindmap) aus den vorhandenen Backlog-Items und ordnest die
Items den Knoten zu. Das Feld „Area“ gibt es nicht mehr; die Einordnung nach Themen läuft nur noch über die Knoten.
Arbeite automatisch durch, ohne Rückfrage je Knoten; am Ende gibst du einen Bericht. Nur wenn das Projekt nicht
eindeutig ist oder ein Werkzeug dauerhaft fehlschlägt, fragst du den Owner.

## Werkzeuge

Du arbeitest nur mit den MCP-Tools des Viewers (Server `todo-viewer`): `workspace_list_projects`,
`backlog_index_lines`, `backlog_get_item`, `mindmap_list_maps`, `mindmap_get_tree`, `mindmap_create_node`,
`mindmap_assign_item`. Nicht die Dateien `TODO.md`, `archive.md` oder `items/` lesen oder ändern, keine Skripte
(`backlog_api.py`), keine anderen Wege. Fehlt ein genanntes Tool, brich ab und sage, welches fehlt. Alle Tools
liefern JSON; ein Fehler hat `code` und `message`.

## Ablauf

1. **Projekt bestimmen.** `workspace_list_projects` aufrufen; das Projekt ist das, dessen Name oder Ordner zu diesem
   Checkout passt (bei nur einem Projekt dieses). Merke dir seine `uid` als `PROJECT`; sie geht in jeden Aufruf mit
   `project`. Ist die Wahl nicht eindeutig, frage den Owner.
2. **Bestand lesen.** `mindmap_get_tree` mit `project=PROJECT` aufrufen (ohne `tree`: das ist der Themenbaum des
   Projekts). `nodes` sind die vorhandenen Knoten (mit `uid`, `label`, `parent_uid`, `title`), `unassigned` die Items ohne Knoten.
   Ist der Baum nicht leer, erweiterst du ihn: vorhandene Knoten bleiben, nichts wird doppelt angelegt, bereits
   zugeordnete Items bleiben, wo sie sind.
3. **Items lesen.** `backlog_index_lines` mit `projects=PROJECT` ohne Statusfilter: alle Items, auch `Completed` und
   `Rejected`. Lies `backlog_get_item` für jedes Epic und jede Story (Titel, Ziel, Abschlusskriterien, Kinder) und
   für Tasks nur, wenn Titel und Parent die Zuordnung nicht klären. Gelöschte Items zählen nicht. Die alten
   Area-Werte gibt es nicht mehr; Grundlage sind Titel, Ziel und Text.
4. **Themen bilden.** Entwirf den Baum, bevor du etwas anlegst:
   - Knoten sind **Themen** (was der Owner mit dem Projekt erreichen will oder woran er denkt), keine technischen
     Schichten: kein Knoten „Web-UI“, „Backend“, „Datenbank“ oder „API“ als Einordnung, auch nicht als Oberknoten.
   - Epics sind oft selbst Themen oder liefern deren Namen; Stories und Tasks ohne Epic gehören zum passenden Thema.
   - Gleiche Themen bündeln; derselbe Gedanke in zwei Knoten ist ein Fehler. Ein Thema bekommt einen Knoten nur,
     wenn mindestens ein Item darunterfällt oder es ein Oberthema für mindestens zwei Unterthemen ist.
   - So viele Ebenen wie nötig, so wenige wie möglich; höchstens etwa sieben Knoten je Ebene; höchstens drei Ebenen,
     solange das Projekt nicht deutlich größer ist.
   - Titel kurz (ein bis vier Wörter), in der Sprache des Projekts, ohne Nummern und ohne Item-Kennungen.
   - Bei einem nicht leeren Baum: neue Themen unter den passenden vorhandenen Knoten einhängen.
5. **Anlegen.** `mindmap_create_node` mit `project=PROJECT`, `title` und für Unterthemen `parent` (die `uid` des
   Parent-Knotens aus der Antwort des vorigen Aufrufs); von oben nach unten, Parent vor Kind. `text` nur, wenn der
   Titel allein missverständlich wäre. Merke dir die `uid` jedes Knotens.
6. **Zuordnen.** `mindmap_assign_item` mit `node` (Knoten-`uid`), `item` (Label wie `STORY-004` oder `uid`) und
   `project=PROJECT`:
   - Zuerst jedes **Epic**. Seine Kinder (Stories, Tasks) erben den Knoten und werden nicht einzeln zugeordnet.
   - Dann **Stories und Tasks ohne Epic**, jeweils dem passendsten Knoten.
   - Ein Kind nur dann eigens zuordnen, wenn es thematisch woanders hingehört als sein Parent.
   - Abgeschlossene und abgelehnte Items werden genauso zugeordnet wie offene.
   - `mindmap_item_assigned` heißt: das Item hat schon einen Knoten. Dann **nicht** `replace` setzen; lass es dort
     und nenne es im Bericht.
7. **Prüfen.** `mindmap_get_tree` erneut lesen. `unassigned` muss leer sein, sonst ordne nach oder nenne jedes
   verbleibende Item mit Grund im Bericht. Prüfe stichprobenweise mit `mindmap_get_item_node` (Parameter `item`,
   `project`), dass der wirksame Knoten stimmt.

## Verboten

- Items ändern, verschieben (`backlog_move_item`), umtypisieren, schließen, wieder öffnen, löschen, ihre Notizen oder
  Dokumente schreiben: Kein Item wird verändert; du hängst es nur an einen Knoten.
- Knoten oder Items endgültig löschen; Knoten umbenennen, verschieben oder löschen, die schon da waren.
- Memos oder Wecker anlegen, Einstellungen ändern, Dateien im Checkout ändern.
- Eine Zuordnung mit `replace` ersetzen.
- Werkzeuge, die dieser Prompt nicht nennt, nur lesend und nur, wenn du sonst nicht weiterkommst.

## Bericht

Gib am Ende aus:

1. Der Baum als eingerückte Liste: Knotentitel, Anzahl der Items in Klammern: der Wert `total` des Knotens (Items des Knotens
   einschließlich der geerbten und der Unterknoten).
2. Die Items, die nicht zugeordnet sind oder deren Knoten du nur vermutest, je mit Kennung, Titel und Grund.
3. Was unklar war oder wo du eine Entscheidung treffen musstest (z. B. zwei passende Themen), damit der Owner den
   Baum danach in der Mindmap ändern kann.
4. Eine Zeile: „Items verändert: 0“, nachdem du `backlog_index_lines` noch einmal gelesen hast und es zur Zeit vor
   dem Start passt (Anzahl und Status gleich).

---
