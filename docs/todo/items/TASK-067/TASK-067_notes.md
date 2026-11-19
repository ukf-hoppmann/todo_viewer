# TASK-067 — Mindmap: Papierkorb-Ansicht, Knoten per Ziehen reaktivieren

## State

- Goal/Status: Umgesetzt (Server-Leseoperation, Oberfläche, Doku), Tests grün; wartet auf Bestätigung des Owners.
- Next step: Owner prüft „Papierkorb anzeigen“ → Ast aus der Seitenansicht auf eine Stelle der Karte ziehen. Die Kette `TASK-062` → `TASK-063` → `TASK-066` → `TASK-067` ist damit zu Ende.
- Open:
  - Keine
- Decided:
  - Eigene Seitenansicht „Papierkorb“ mit den gelöschten Knoten des Projekts, ein- und ausschaltbar wie „Nicht zugeordnet“ (2026-11-19)
  - Ziehen eines Knotens an eine neue Stelle reaktiviert ihn dort (Backend: wiederherstellen und umziehen aus `TASK-063`) (2026-11-19)
  - Die neue Stelle ersetzt die alte Platzierung im aktuellen Baum, Platzierungen in anderen Bäumen kommen wie vorher zurück (2026-11-19)
  - Vorsichtige Annahmen bei der Umsetzung, siehe Eintrag „Umsetzung“ (2026-11-19)
- References: Spec `TASK-067_spec.md`; Story-Spec `STORY-102_spec.md`; Vorgänger `TASK-063`

State confirmed after entry 2026-11-19 — Umsetzung (783046ff1272)

## 2026-11-19 — Übernahme der Entscheidungen aus STORY-102

### Discussed

- Der Owner will gelöschte Knoten per Ziehen an eine andere Stelle setzen. Die Mindmap-Seite hat bisher keine Papierkorb-Ansicht; Wiederherstellen läuft über den Workspace. Die Ansicht ist neu und wird als eigener Task geführt, damit `TASK-063` nicht zu groß wird (Owner).

### Decided

- Eigener Task, abhängig von `TASK-063`; das Backend bleibt in `TASK-063`.
- Wohin ein Knoten mit mehreren früheren Platzierungen kommt: neue Stelle ersetzt die alte im aktuellen Baum, andere Bäume wie vorher (Owner).

### Open

- Keine

## 2026-11-19 — Umsetzung

### Discussed

- Die Seitenansicht braucht eine Liste der gelöschten Äste je Map. Der Workspace-Papierkorb (`workspace_list_trash`) kennt Knoten nur flach, ohne Baum und ohne Parent; daraus ließen sich die Astspitzen nicht bestimmen.

### Decided

- Neue lesende Operation `list_trashed_nodes` (GET `/api/mindmap/trash/{project}?tree=`, auch MCP): je gelöschtem Knoten mit gültiger Platzierung in der Map, dessen Parent dort nicht ebenfalls gelöscht ist, mit Label, Titel, Version (Token für `restore_and_move_node`), altem Parent und Zahl der gelöschten Knoten des Asts. Server: `trashed_branches` in `application/branches.py`; Tests: `test_mindmap_trashed_nodes.py`.
- Oberfläche: `TrashPanel`, Schalter `showTrash` in `MapFilters`, `restorePlacement` in `domain/tree.ts`, `restoreAndMoveNode` beim Ablegen; Tag `Trashed` wird von Server-Ereignissen neu geladen.

### Vorsichtige Annahmen

- Die Ansicht zeigt die gelöschten Äste der **gezeigten Map** (Projektbaum oder freie Map), nicht aller Maps des Projekts: „wiederherstellen und umziehen“ verlangt eine Platzierung im Baum, und die neue Stelle ersetzt die alte in genau diesem Baum. So führt jedes Ziehen auf eine Stelle der Karte zu einem erlaubten Fall; ein Ast, der nur in einer anderen Map stand, erscheint dort.
- Gezeigt wird je Ast nur der oberste gelöschte Knoten; gelöschte Unterknoten kommen beim Ziehen mit (Zahl am Eintrag). Ein einzelner gelöschter Unterknoten unter einem lebenden Parent ist ein eigener Eintrag.
- Der Schalter ist standardmäßig **aus** (anders als „Nicht zugeordnet“), weil der Papierkorb meist leer oder selten gebraucht ist; er gilt nur in der Einzelansicht.
- Auf die Wurzel lässt sich „hinein“ ziehen (unter die Wurzel, ans Ende), nie davor oder dahinter; sonst gelten dieselben Stellen wie beim Umhängen, aber ohne die Regeln gegen Kreise (der Ast ist nicht im Baum). Was nur der Server prüft (z. B. `mindmap_parent_in_trash` für andere Bäume), zeigt die Seite als Meldung; der Eintrag bleibt dann in der Liste.

### Geprüft

- Server: `pytest tests/implementation/integration/server/plugins/mindmap` und `unit/server` grün; `mypy` für das Plugin grün; `ruff check` meldet nur die zwei Altfunde.
- Client: Vitest gesamt (121 Dateien, 1474 Tests) grün, darunter neue Tests für `restorePlacement`, die Seitenansicht (Schalter, Liste, Ziehen hinein/davor/danach/Wurzel, Ablehnung, Map-Wechsel, Gesamtansicht) und den Filter; `npm run lint` meldet nur die 5 Altfehler in `usePersistentState.ts`.
- Nicht gelaufen: Server-Gesamtsuite (nur Mindmap- und Unit-Tests); Ziehen im echten Browser (React Flow ist in den Tests ersetzt).
