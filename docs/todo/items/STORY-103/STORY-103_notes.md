# STORY-103 — Ideen-Knoten ins Backlog überführen

## State

- Goal/Status: Geplant; noch ohne Tasks, weil zwei Fragen offen sind; Typwahl ist entschieden.
- Next step: Restliche offene Fragen mit dem Owner klären (Tiefe über drei Ebenen, Memo), dann Spec nachziehen und bei Bedarf in Tasks teilen.
- Open:
  - Knoten tiefer als drei Ebenen: Vorschlag ist, sie als Stichpunkte in die Beschreibung des Tasks zu schreiben statt sie zu verwerfen (2026-11-13)
  - Ob sich ein Ideen-Knoten auch zu einem Memo machen lässt, nicht nur zu einem Backlog-Item (2026-11-13)
- Decided:
  - Alles oder Teile einer Map lassen sich ins Backlog überführen (Ausgangsidee des Owners) (2026-11-13)
  - Beim Überführen bleibt der Knoten stehen und das neue Item wird daran gehängt; der Zustand des Knotens ändert sich dadurch von selbst (2026-11-13)
  - Der Typ eines Items wird nicht automatisch aus der Ebene des Knotens abgeleitet; Mensch oder KI legen ihn je Knoten fest, weil Kind-Äste Abhängigkeiten oder Parent-Child-Beziehungen sein können (2026-11-23)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`; Story STORY-086

State confirmed after entry 2026-11-23 — Typwahl beim Überführen eines Astes (d306ba749759)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `TASK-064`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.
- Verwandt: die Umwandeln-Regeln aus Story STORY-086 und die Beförderung eines Memos zum Item.

### Decided

- Alles oder Teile einer Map lassen sich ins Backlog überführen (Ausgangsidee des Owners)
- Beim Überführen bleibt der Knoten stehen und das neue Item wird daran gehängt; der Zustand des Knotens ändert sich dadurch von selbst

### Open

- Typwahl beim Überführen eines Astes: Vorschlag nach Ebene (oberster Knoten Epic, darunter Story, darunter Task) mit Änderung in der Vorschau
- Knoten tiefer als drei Ebenen: Vorschlag ist, sie als Stichpunkte in die Beschreibung des Tasks zu schreiben statt sie zu verwerfen

## 2026-11-13 — Nachtrag aus der Ideensammlung

### Discussed

- Beim Abgleich mit dem Protokoll in Task TASK-064 fehlte ein früher offener Punkt: ob aus einer Idee auch ein Memo werden kann. Der Owner hat später festgelegt, dass Memos anders sind als der Backlog und sich an Knoten nur verlinken lassen; über das Überführen in ein Memo wurde nicht entschieden.

### Decided

- Nichts.

### Open

- Ob sich ein Ideen-Knoten auch zu einem Memo machen lässt.

## 2026-11-23 — Typwahl beim Überführen eines Astes

### Discussed

- Frage: Welchen Typ bekommen die Items, wenn ein Ast überführt wird?
- Option A: Typ nach Ebene vorbelegen (oberster Knoten Epic, darunter Story, darunter Task), in der Vorschau änderbar; ergänzt um die Tiefe im Backlog, wenn der Ast unter einem bestehenden Item hängt. Vorteil: meist sofort gültig. Nachteil: passt nicht für jeden Ast.
- Option B: alles als Task. Geht an der Struktur des Backlogs vorbei.
- Option C: Typ immer ausdrücklich festlegen, ohne Vorgabe. Flexibel, bei großen Ästen mehr Aufwand.
- Empfehlung war A mit Ergänzung.
- Der Owner lehnt die pauschale Ableitung ab: Was ein Ast wird, hängt vom Ast ab. Die Kind-Äste können abhängige Tasks oder Stories sein, aber auch Parent-Child-Beziehungen.

### Decided

- Option C: Der Typ wird nicht aus der Ebene abgeleitet. Das Überführen eines Astes macht ein Mensch oder die KI, die für jeden Knoten Typ (und Beziehung) festlegen. Grund: Die Form des Astes bestimmt den Typ, nicht seine Ebene.
- Verworfen: Option A, weil die Ebene den Typ nicht bestimmt; Option B, weil sie die Struktur des Backlogs ignoriert.

### Open

- Folge für die Spec: Kriterium 2 (Vorschau mit änderbaren Typen) und die Frage, wie je Knoten zwischen Parent-Child und Abhängigkeit gewählt wird, müssen angepasst werden.
- Knoten tiefer als drei Ebenen: Vorschlag, sie als Stichpunkte in die Beschreibung des Tasks zu schreiben (offen aus 2026-11-13).
- Ob sich ein Ideen-Knoten auch zu einem Memo machen lässt (offen aus 2026-11-13).
