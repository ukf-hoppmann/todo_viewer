# STORY-099 — Mindmap-Gerüst: Themenbaum je Projekt anlegen, ordnen und mit Notizen versehen

## State

- Goal/Status: Umgesetzt, wartet auf Bestätigung des Owners (2026-11-16); `TASK-052` (Server), `TASK-053` (Seite), `TASK-054` (Ziehen) und `TASK-055` (Notizen) sind abgeschlossen und in `todo_mindmap`.
- Next step: Owner prüft die Story und bestätigt sie; danach Archivierung.
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
  - Plan freigegeben; ein Task je Session auf eigenem `claude/…`-Branch, gemergt nach `todo_mindmap`, nacheinander (2026-11-16)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`

State confirmed after entry 2026-11-16 — Kriterien geprüft (a343a7d99343)

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

## 2026-11-16 — Umsetzungsplan freigegeben, Sessions

### Discussed

- Plan für `STORY-099`: Server-Plugin `mindmap` (`TASK-052`), Seite (`TASK-053`), Ziehen (`TASK-054`), Notizen (`TASK-055`); die Tasks bauen aufeinander auf.
- Wo die Sessions arbeiten: eigene `claude/…`-Branches oder direkt auf `todo_mindmap`.

### Decided

- Der Umsetzungsplan für `STORY-099` ist vom Owner freigegeben
- Jeder Task läuft in einer eigenen neuen Session auf einem eigenen `claude/…`-Branch; gemergt wird immer nach `todo_mindmap`
- Die Tasks laufen nacheinander; die nächste Session startet erst, wenn die vorige gemergt ist

### Open

- Wo die Dokument-Logik für Knoten liegt (gemeinsamer Baustein im Workspace oder `requires: backlog`): vor `TASK-055` klären

## 2026-11-16 — TASK-053 abgeschlossen

### Discussed

- Die Mindmap-Seite ist umgesetzt und vom Owner bestätigt; Einzelheiten und Entscheidungen stehen in den Notizen von `TASK-053`.
- Die Detailspalte zeigt schon Titel und Text des Knotens; `TASK-055` ergänzt dort die Dokumente.

### Decided

- `TASK-053` ist `Completed` und nach `todo_mindmap` gemergt


## 2026-11-16 — TASK-055 abgeschlossen

### Discussed

- Die Notizen an Knoten sind umgesetzt und vom Owner bestätigt; Einzelheiten und Entscheidungen stehen in den Notizen von `TASK-055`.

### Decided

- Ort der Dokument-Logik: eigene Tabelle `mindmap_documents` im Plugin `mindmap` (Open from 2026-11-16 (Ort der Dokument-Logik) resolved)
- `TASK-055` ist `Completed` und nach `todo_mindmap` gemergt

## 2026-11-16 — Kriterien geprüft

### Discussed

- Kriterium 1 (Knoten, Platzierung): erfüllt; Titel, optionaler Text, beliebige Tiefe, leere Knoten, Lage nur als Platzierung (`TASK-052`, Tests `test_tree_rules.py`, `test_mindmap_migration.py`).
- Kriterium 2 (Anlegen, Umbenennen, Umhängen, Papierkorb, Wiederherstellen über API, MCP, Oberfläche; keine Schleife): erfüllt. Anlegen, Ändern und Umhängen sind eigene Operationen, Papierkorb und Wiederherstellen laufen über `workspace` (API, MCP und die Papierkorb-Seite); Kreise lehnt der Server ab (`mindmap_loop`) und die Map bietet sie nicht an (`TASK-054`). Im Browser geprüft: Knoten in der Map in den Papierkorb legen, auf der Papierkorb-Seite zurückholen, er steht wieder in der Map.
- Kriterium 3 (Seite, zwei Ebenen offen): erfüllt (`TASK-053`).
- Kriterium 4 (Abschnitt „Dokumente“): erfüllt (`TASK-055`).
- Kriterium 5 (Tests): Server 1153 und Client 1245 grün; ausgenommen `test_client_log.py::test_browser_entry_lands_in_the_server_log`, der schon vorher fehlschlug und die Mindmap nicht betrifft.

### Decided

- `STORY-099` steht auf `Awaiting confirmation`

### Open

- Markierungen für Ideen-Knoten („verworfen“, „später“): Form und Story offen, kein Teil dieser Story
