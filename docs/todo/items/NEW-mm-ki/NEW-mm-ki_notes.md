# NEW-mm-ki — KI ordnet neue Items der Mindmap zu und schlägt Knoten vor

## State

- Goal/Status: Geplant; noch ohne Tasks, weil die Form der Vorschläge offen ist.
- Next step: Form der Vorschläge mit dem Owner klären.
- Open:
  - Form der Vorschläge: nur im Gespräch oder als sichtbarer Vorschlag in der Oberfläche, den man dort bestätigt (2026-11-13)
  - Die Regel für die KI gehört in den Skill von Claude_Harness; wie sie dorthin kommt, ist zu klären (siehe auch Story STORY-092) (2026-11-13)
- Decided:
  - Die KI überlegt beim Anlegen eines Items, wohin es passt, und füttert die Map so nebenbei (2026-11-13)
  - Die KI darf Knoten und Unterknoten vorschlagen und legt sie nach Bestätigung an; ohne Bestätigung erfindet sie keine Themen (2026-11-13)
  - Clustern läuft über gespeicherte Knoten, nicht über eine Berechnung bei jedem Öffnen; der Viewer braucht keine eigene LLM-Anbindung (2026-11-13)
  - Verworfen: Clustern über Textähnlichkeit der Titel, zu schwach bei kurzen Titeln (2026-11-13)
- References: Konzept `NEW-mindmap_spec.md` im Epic `NEW-mindmap`; Ideensammlung `NEW-mindmap-machbarkeit`; Story STORY-092

State confirmed after entry 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung (257f7b0d6577)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `NEW-mindmap-machbarkeit`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.
- Ein Startvorschlag ohne KI wäre aus Area, gemeinsamem Epic und Abhängigkeitsgruppen (`connectedComponents`) möglich; er ist nicht Teil dieser Story, solange der Owner ihn nicht wünscht.

### Decided

- Die KI überlegt beim Anlegen eines Items, wohin es passt, und füttert die Map so nebenbei
- Die KI darf Knoten und Unterknoten vorschlagen und legt sie nach Bestätigung an; ohne Bestätigung erfindet sie keine Themen
- Clustern läuft über gespeicherte Knoten, nicht über eine Berechnung bei jedem Öffnen; der Viewer braucht keine eigene LLM-Anbindung
- Verworfen: Clustern über Textähnlichkeit der Titel, zu schwach bei kurzen Titeln

### Open

- Form der Vorschläge: nur im Gespräch oder als sichtbarer Vorschlag in der Oberfläche, den man dort bestätigt
- Die Regel für die KI gehört in den Skill von Claude_Harness; wie sie dorthin kommt, ist zu klären (siehe auch Story STORY-092)
