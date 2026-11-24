# TASK-072 — Prompts: Themenbaum aus den Items erzeugen und Claude_Harness anpassen

## State

- Goal/Status: Beide Prompts geschrieben; der Themenbaum-Prompt ist gegen einen echten Server mit Beispielprojekt erprobt; wartet auf die Abnahme (2026-11-24).
- Next step: Owner prüft die Prompts (`TASK-072_spec_prompt-baum.md`, `TASK-072_spec_prompt-harness.md`) und nimmt die Task ab; danach den Baum-Prompt je Projekt ausführen lassen.
- Open:
  - Nichts offen (2026-11-24)
- Decided:
  - Der Themenbaum entsteht automatisch durch eine KI aus Titel, Ziel und Text der Items; der Owner bekommt dafür einen Prompt (Owner, `STORY-106`) (2026-11-23)
  - Die KI übergibt an Claude_Harness nichts selbst; der Owner bekommt den Prompt (Owner, `STORY-106`) (2026-11-23)
  - Der Baum-Prompt arbeitet nur mit sieben MCP-Tools, ändert kein Item und ersetzt keine Zuordnung (2026-11-24)
  - Der Harness-Prompt beschränkt sich auf Area und Format Version 3; der Mindmap-Spiegel ist Sache von `TASK-082` (2026-11-24)
- References: Specs `TASK-072_spec.md`, `TASK-072_spec_prompt-baum.md`, `TASK-072_spec_prompt-harness.md`; Story `STORY-106`; Abhängigkeiten: TASK-071

State confirmed after entry 2026-11-24 — Umsetzung: beide Prompts und Erprobung (818b54c98605)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-106

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-106 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-106_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Der Themenbaum entsteht automatisch durch eine KI aus Titel, Ziel und Text der Items; der Owner bekommt dafür einen Prompt (Owner, `STORY-106`)
- Die KI übergibt an Claude_Harness nichts selbst; der Owner bekommt den Prompt (Owner, `STORY-106`)

### Open

- Nichts.

## 2026-11-24 — Umsetzung: beide Prompts und Erprobung

### Discussed

- Baum-Prompt: Die Werkzeugnamen und Parameter stammen aus `tools/list` des laufenden Servers (Stand nach `TASK-071`), nicht aus dem Gedächtnis.
- Erprobung: frischer Server mit dem ganzen Viewer, Beispielprojekt mit 20 Items (3 Epics, Stories, Tasks, ein abgeschlossenes, ein abgelehntes, ohne Knoten). Der Ablauf des Prompts wurde Schritt für Schritt über MCP ausgeführt: sechs Knoten (zwei Ebenen) angelegt, 9 Zuordnungen (3 Epics, einzelne Stories und Tasks ohne Epic); die Kinder erben.
- Ergebnis: danach 0 Items unter „Nicht zugeordnet“; ein Vorher/Nachher-Vergleich aller 20 Items (alle Felder) ist identisch, also kein Item verändert; ein zweites Zuordnen scheitert ohne `replace` mit `mindmap_item_assigned`, wie der Prompt es voraussetzt.
- Beobachtungen, die in den Prompt eingeflossen sind: die Knoten tragen `parent_uid` (nicht `parent`) und `label`; `total` zählt auch die Unterknoten; ohne Statusfilter gehören abgeschlossene und abgelehnte Items zu den Items ohne Knoten, also werden sie mit zugeordnet.
- Grenze der Erprobung: Der Ablauf wurde von mir nach dem Prompt ausgeführt, nicht von einer frischen Sitzung nur mit dem Prompt; die Qualität der Themenwahl bei einem echten Projekt zeigt sich erst beim Owner.
- Harness-Prompt: Die Fundorte stammen aus der kopierten Fassung des Harness in diesem Repository (Skill `todo`, `format.md`, `api.md`, `memos*.md`, `backlog.py`, `backlog_api.py`, `memos_api.py`, Vorlagen); die Änderungen aus den Techdocs (`interfaces.md`) und aus dem Verhalten des Servers (`area` in `fields` → `not_editable`).
- Der Prompt für Claude_Harness enthält keine Mindmap-Spiegel-Änderungen, damit er sich nicht mit `TASK-082` überschneidet.

### Decided

- Beide Prompts liegen als Spec-Dateien neben der Spec; der Owner erhält sie vollständig im Text am Ende der Sitzung.
- Die KI übergibt nichts selbst an Claude_Harness.

### Open

- Nichts.
