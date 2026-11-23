# STORY-104 — KI ordnet neue Items der Mindmap zu und schlägt Knoten vor

## State

- Goal/Status: Geplant; noch ohne Tasks; Form der Vorschläge entschieden, Weg der KI-Regel nach Claude_Harness offen.
- Next step: Weg der KI-Regel mit dem Owner klären, dann Spec und Aufteilung in Tasks.
- Open:
  - Die Regel für die KI gehört in den Skill von Claude_Harness; wie sie dorthin kommt, ist zu klären (siehe auch Story STORY-092) (2026-11-13)
- Decided:
  - Die KI überlegt beim Anlegen eines Items, wohin es passt, und füttert die Map so nebenbei (2026-11-13)
  - Die KI darf Knoten und Unterknoten vorschlagen und legt sie nach Bestätigung an; ohne Bestätigung erfindet sie keine Themen (2026-11-13)
  - Clustern läuft über gespeicherte Knoten, nicht über eine Berechnung bei jedem Öffnen; der Viewer braucht keine eigene LLM-Anbindung (2026-11-13)
  - Verworfen: Clustern über Textähnlichkeit der Titel, zu schwach bei kurzen Titeln (2026-11-13)
  - Die KI schlägt neue Knoten im Gespräch vor; nach der Bestätigung legt sie sie über API und MCP an. Ohne Bestätigung entsteht kein Knoten und das Item landet unter „Nicht zugeordnet“ (2026-11-23)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`; Story STORY-092

State confirmed after entry 2026-11-23 — Form der Knoten-Vorschläge (3bab3d227d5f)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `TASK-064`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.
- Ein Startvorschlag ohne KI wäre aus Area, gemeinsamem Epic und Abhängigkeitsgruppen (`connectedComponents`) möglich; er ist nicht Teil dieser Story, solange der Owner ihn nicht wünscht.

### Decided

- Die KI überlegt beim Anlegen eines Items, wohin es passt, und füttert die Map so nebenbei
- Die KI darf Knoten und Unterknoten vorschlagen und legt sie nach Bestätigung an; ohne Bestätigung erfindet sie keine Themen
- Clustern läuft über gespeicherte Knoten, nicht über eine Berechnung bei jedem Öffnen; der Viewer braucht keine eigene LLM-Anbindung
- Verworfen: Clustern über Textähnlichkeit der Titel, zu schwach bei kurzen Titeln

### Open

- Form der Vorschläge: nur im Gespräch oder als sichtbarer Vorschlag in der Oberfläche, den man dort bestätigt
- Die Regel für die KI gehört in den Skill von Claude_Harness; wie sie dorthin kommt, ist zu klären (siehe auch Story STORY-092)

## 2026-11-23 — Form der Knoten-Vorschläge

### Discussed

- Frage: Wo bestätigt der Owner einen Knoten-Vorschlag der KI?
- Option A: im Gespräch; die KI fragt im Chat und legt nach dem Ja den Knoten an. Einfach, nichts Neues im Viewer; der Vorschlag lebt nur in der Sitzung.
- Option B: sichtbarer Vorschlag in der Oberfläche, der dort bestätigt wird. Bleibt stehen und passt zu Cloud-Sitzungen, braucht aber Zustand, API, MCP und UI.
- Option C: Gespräch, und ohne Antwort bleibt das Item „Nicht zugeordnet“, ohne gespeicherten Vorschlag.
- Empfehlung war A: Kriterium 2 sichert das Verhalten ohne Bestätigung schon ab.

### Decided

- Option A: Vorschläge laufen im Gespräch. Ohne Bestätigung entsteht kein Knoten, das Item landet unter „Nicht zugeordnet“.
- Verworfen vorerst: Option B wegen des Aufwands; sie kann später kommen, wenn Vorschläge in unbeaufsichtigten Sitzungen verloren gehen.

### Open

- Wie die Regel für die KI in den Skill von Claude_Harness kommt (offen aus 2026-11-13).
