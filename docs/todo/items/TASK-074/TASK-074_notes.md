# TASK-074 — Server: einen Ast mit Vorschau ins Backlog überführen

## State

- Goal/Status: Umgesetzt und getestet (Server-Suite komplett grün); wartet auf die Abnahme des Owners.
- Next step: Abnahme; danach `TASK-076` (Oberfläche Ast) auf Basis von `preview_branch_transfer` und `transfer_branch`.
- Open:
  - Nichts offen für die Abnahme (2026-11-24)
- Decided:
  - Kein Automatismus nach Ebene oder Tiefe; jeder Ast wird einzeln von Mensch oder KI entschieden; ein Knoten in Tiefe 5 kann ein eigenes Epic sein (Owner) (2026-11-23)
  - Die Backlog-Regeln werden nicht in der Mindmap nachgebaut; das Plugin backlog prüft mit denselben Regeln wie beim Anlegen (2026-11-24)
  - Kein Rückbau bei Teilfehlern; Nachfolger eines gescheiterten Eintrags werden nicht versucht (2026-11-24)
  - HTTP-Routen `/nodes/{root}/preview-branch-transfer` und `/transfer-branch`, weil `/transfer` schon `transfer_node_to_map` gehört (2026-11-24)
- References: Spec `TASK-074_spec.md`; Story `STORY-103`; Abhängigkeit TASK-073; Doku `docs/techdocs/neubau-server.md` (Plugin mindmap)

State confirmed after entry 2026-11-24 — Umsetzung (ca83ac5f7822)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-103

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-103 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-103_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Kein Automatismus nach Ebene oder Tiefe; jeder Ast wird einzeln von Mensch oder KI entschieden; ein Knoten in Tiefe 5 kann ein eigenes Epic sein (Owner)
- Die Backlog-Regeln werden nicht in der Mindmap nachgebaut; das Plugin backlog bekommt eine nicht schreibende Prüfung (Zuschnitt)
- Kein Rückbau bei Teilfehlern; die Vorschau soll sie vorher abfangen (Zuschnitt)

### Open

- Nichts.

## 2026-11-24 — Umsetzung

### Discussed

- Die gesammelte Prüfung steht in `LifecycleRules.introduced` (`check_change` wirft die erste daraus); das Backlog bekommt `EditService.check_new_items` über `domain/planning.py`. Die Mindmap ruft sie über den Port `BacklogChecker` auf.
- Die Route `/nodes/{root}/transfer` war durch `transfer_node_to_map` belegt; die neuen Routen heißen `preview-branch-transfer` und `transfer-branch`.
- `parent_type_not_allowed` ist der Code für `epic_with_parent`; das Backlog verbietet sonst keine Typkombination (z. B. Story unter Task), das Verhalten wurde nicht geändert.
- Ist ein Eintrag selbst mangelhaft (z. B. Kriterien fehlen), meldet die Vorschau Folgeprobleme (Kreise) an ihm nicht; sie erscheinen, sobald er behoben ist.

### Decided

- Die Entscheidungen der Spec gelten unverändert; die Routennamen wie oben.

### Open

- Nichts.
