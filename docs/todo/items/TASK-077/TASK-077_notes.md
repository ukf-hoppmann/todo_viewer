# TASK-077 — MCP-Tools nennen die Regel zum Zuordnen und Vorschlagen

## State

- Goal/Status: Umgesetzt und verifiziert (Server- und Client-Tests grün); wartet auf die Abnahme des Owners.
- Next step: Abnahme durch den Owner; danach `TASK-078` (Systemtest und Prompt für Claude_Harness).
- Open:
  - Nichts offen (2026-11-24)
- Decided:
  - Die Regel steht in den MCP-Tool-Beschreibungen des Viewers und zusätzlich als Skill-Regel in Claude_Harness (Owner) (2026-11-23)
  - Die Beschreibung von backlog_create_item enthält nur einen Texthinweis, weil backlog die Mindmap nicht kennen darf (Architektur §1; Zuschnitt) (2026-11-23)
  - Ein gemeinsamer Satz `ASSIGNMENT_RULE` in `mindmap/application/guidance.py` an vier Tools (2026-11-24)
- References: Spec `TASK-077_spec.md`; Story `STORY-104`; Abhängigkeiten: TASK-073; Folge: TASK-078

State confirmed after entry 2026-11-24 — Umsetzung (819c39cc9b56)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-104

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-104 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-104_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Die Regel steht in den MCP-Tool-Beschreibungen des Viewers und zusätzlich als Skill-Regel in Claude_Harness (Owner)
- Die Beschreibung von backlog_create_item enthält nur einen Texthinweis, weil backlog die Mindmap nicht kennen darf (Architektur §1; Zuschnitt)

### Open

- Nichts.

## 2026-11-24 — Umsetzung

### Discussed

- Test zuerst: `test_tool_descriptions.py` (6 Fälle) rot gesehen (Modul `guidance` fehlte), dann `application/guidance.py` mit `ASSIGNMENT_RULE` und Anhängen an die vier Mindmap-Tools; `backlog_create_item` bekam nur den Texthinweis.
- Die Beschreibungen stehen im OpenAPI-Schema; die Client-Typen (`schema.d.ts`) wurden mit `scripts/gen-api.sh` neu erzeugt, sonst schlägt `test_openapi_types` fehl.
- Kriterium 3 und 4 brauchen keinen neuen Code: `get_tree`, `assign_item`, `create_node`, `create_item_at_node` gibt es; `get_tree` zeigt `unassigned` schon. Der Systemtest dazu folgt in `TASK-078`.
- Vor der Umsetzung die Server-Suite einmal komplett laufen lassen (Auftrag): grün, nichts Auffälliges aus `TASK-073`.

### Decided

- Der Regeltext steht als eine Konstante an einer Stelle und wird per Zeichenkette angehängt.

### Open

- Nichts.
