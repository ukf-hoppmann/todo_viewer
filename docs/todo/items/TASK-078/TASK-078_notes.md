# TASK-078 — Systemtest Zuordnen und Vorschlagen; Prompt für Claude_Harness

## State

- Goal/Status: Umgesetzt und verifiziert (Server 1509 und Client 1490 Tests grün); wartet auf die Abnahme des Owners.
- Next step: Abnahme durch den Owner; danach kann `STORY-104` abgenommen werden. Der Owner gibt den Prompt aus `TASK-078_spec_prompt-harness.md` selbst an Claude_Harness.
- Open:
  - Nichts offen (2026-11-24)
- Decided:
  - Der Owner übergibt die Regel selbst; die KI liefert den Prompt (Owner) (2026-11-23)
  - Der Systemtest bildet das Gespräch durch getrennte Aufrufe nach, weil der Vorschlag keinen Zustand im Server hat (Zuschnitt) (2026-11-23)
  - Der Test steht als zweiter Test in `test_harness_flow.py`, weil die Datei nicht zu lang wird und Fixture und Hilfen dort liegen (2026-11-24)
- References: Spec `TASK-078_spec.md`, Prompt `TASK-078_spec_prompt-harness.md`; Story `STORY-104` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: TASK-077

State confirmed after entry 2026-11-24 — Umsetzung (6052d03fd9c2)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-104

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-104 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-104_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Der Owner übergibt die Regel selbst; die KI liefert den Prompt (Owner)
- Der Systemtest bildet das Gespräch durch getrennte Aufrufe nach, weil der Vorschlag keinen Zustand im Server hat (Zuschnitt)

### Open

- Nichts.

## 2026-11-24 — Umsetzung

### Discussed

- Der Ablauf braucht keinen neuen Servercode: `get_tree`, `create_item_at_node`, `create_node`, `assign_item` und `get_item_node` gibt es. Der Test `test_the_ai_assigns_items_to_the_topic_tree_and_proposes_nodes_only_after_consent` deckt vier Schritte ab: Item am passenden Knoten (Knoten wechselt zu „planned“), Item ohne Knoten bleibt „Nicht zugeordnet“ ohne neuen Knoten, nach simulierter Zustimmung Knoten anlegen und zuordnen, bei verweigerter Zustimmung bleibt Baum unverändert.
- Test zuerst war hier nicht sinnvoll: das Verhalten besteht schon, der Test sichert es nur ab; er lief beim ersten Versuch grün.
- Der Prompt für Claude_Harness steht in `TASK-078_spec_prompt-harness.md`; Werkzeugnamen und Beschreibungen mit `tools/list` gegen den laufenden Viewer geprüft. Er bittet nur um die Regel für den API-Modus; der Dateimodus folgt mit `STORY-105`.
- Doku: `tests/README.md` und `docs/techdocs/interfaces.md` nennen den neuen Test.

### Decided

- Zweiter Test in `test_harness_flow.py` statt neuer Datei

### Open

- Nichts.
