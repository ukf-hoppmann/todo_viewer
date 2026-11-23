# STORY-104 — KI ordnet neue Items der Mindmap zu und schlägt Knoten vor

## State

- Goal/Status: Geplant; noch ohne Tasks; Form der Vorschläge entschieden, Weg der KI-Regel entschieden; Spec und Aufteilung in Tasks fehlen.
- Next step: Spec schreiben und in Tasks teilen, danach Plan vorlegen.
- Open:
- Decided:
  - Die KI überlegt beim Anlegen eines Items, wohin es passt, und füttert die Map so nebenbei (2026-11-13)
  - Die KI darf Knoten und Unterknoten vorschlagen und legt sie nach Bestätigung an; ohne Bestätigung erfindet sie keine Themen (2026-11-13)
  - Clustern läuft über gespeicherte Knoten, nicht über eine Berechnung bei jedem Öffnen; der Viewer braucht keine eigene LLM-Anbindung (2026-11-13)
  - Verworfen: Clustern über Textähnlichkeit der Titel, zu schwach bei kurzen Titeln (2026-11-13)
  - Die KI schlägt neue Knoten im Gespräch vor; nach der Bestätigung legt sie sie über API und MCP an. Ohne Bestätigung entsteht kein Knoten und das Item landet unter „Nicht zugeordnet“ (2026-11-23)
  - Die Regel für die KI steht in den MCP-Tool-Beschreibungen des Viewers (sofort wirksam) und wird zusätzlich als Skill-Regel an Claude_Harness übergeben; die Übergabe macht der Owner mit einem Prompt, den die KI am Ende der Story liefert (2026-11-23)
  - Kriterium 3 ist entsprechend angepasst (2026-11-23)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`; Story STORY-092

State confirmed after entry 2026-11-23 — Weg der KI-Regel nach Claude_Harness (908edea04b12)

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

## 2026-11-23 — Weg der KI-Regel nach Claude_Harness

### Discussed

- Frage: Wie kommt die Regel „Item einem Knoten zuordnen, Knoten nur nach Bestätigung vorschlagen“ in die Skills von Claude_Harness, das ein eigenes Projekt mit eigenem Backlog ist?
- Option A: Regel hier beschreiben und an das Backlog von Claude_Harness übergeben. Saubere Zuständigkeit, aber bis dahin kennt die KI die Regel nicht.
- Option B: zusätzlich in den MCP-Tool-Beschreibungen des Viewers ablegen. Sofort für jede KI sichtbar, passt zu `STORY-092`; die Regel steht aber an zwei Stellen.
- Empfehlung: A und B. Der Pfad zum Repo von Claude_Harness gilt nur auf dem Mac des Owners, eine Übergabe ist aus der Cloud nicht möglich.

### Decided

- A und B zusammen. Die KI übergibt A nicht selbst: Sie liefert dem Owner einen fertigen Prompt, mit dem er an Claude_Harness tritt. Zeitpunkt: wenn der Systemtest Zuordnen und Vorschlagen abdeckt.
- Kriterium 3 lautet jetzt: Die Regel steht in den MCP-Tool-Beschreibungen, und der Owner hat den fertigen Prompt für Claude_Harness.

### Open

- Nichts offen für die Planung; Spec und Aufteilung in Tasks folgen.
