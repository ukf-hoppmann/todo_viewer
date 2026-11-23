# STORY-103 — Ideen-Knoten ins Backlog überführen

## State

- Goal/Status: Geplant; noch ohne Tasks, weil noch eine Frage offen ist; Typwahl und tiefe Äste sind entschieden.
- Next step: Memo-Frage mit dem Owner klären, dann Spec nachziehen und bei Bedarf in Tasks teilen.
- Open:
  - Wie die Vorschau je Knoten zwischen Parent-Child und Abhängigkeit wählen lässt (2026-11-23)
  - Ob sich ein Ideen-Knoten auch zu einem Memo machen lässt, nicht nur zu einem Backlog-Item (2026-11-13)
- Decided:
  - Alles oder Teile einer Map lassen sich ins Backlog überführen (Ausgangsidee des Owners) (2026-11-13)
  - Beim Überführen bleibt der Knoten stehen und das neue Item wird daran gehängt; der Zustand des Knotens ändert sich dadurch von selbst (2026-11-13)
  - Der Typ eines Items wird nicht automatisch aus der Ebene des Knotens abgeleitet; Mensch oder KI legen ihn je Knoten fest, weil Kind-Äste Abhängigkeiten oder Parent-Child-Beziehungen sein können (2026-11-23)
  - Es gibt keine Automatismen beim Überführen, auch nicht für Äste tiefer als drei Ebenen: Jeder Ast wird einzeln entschieden, ein tiefer Knoten kann ein eigenes Epic werden; die Vorschau prüft nur, was die Struktur erlaubt (2026-11-23)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`; Story STORY-086

State confirmed after entry 2026-11-23 — Äste tiefer als drei Ebenen (936e7e8662cb)

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

## 2026-11-23 — Äste tiefer als drei Ebenen

### Discussed

- Frage: Was geschieht mit Knoten, die tiefer als drei Ebenen liegen, da das Backlog nur Epic, Story und Task kennt?
- Option A: als Stichpunkte in die Beschreibung des untersten Tasks schreiben. Nichts geht verloren, die Stichpunkte sind aber keine eigenen Items.
- Option B: nicht überführen, die Vorschau meldet sie. Sauber, aber der Mensch muss den Ast erst umbauen.
- Option C: je Knoten fragen, mit A als Voreinstellung. Empfehlung war C mit A als Voreinstellung.
- Der Owner: Die Frage lief auf einen Automatismus hinaus, und der passt nicht. Ein Ast der Tiefe 5 kann ein eigenes Epic sein, z. B. Äste 1 bis 4 als Umbau des Backends und Ast 5 als Start des UI-Umbaus, der ein eigenes Epic wäre. Die Tiefe in der Map sagt nichts über die Ebene im Backlog.

### Decided

- Kein Automatismus, auch keine Voreinstellung für tiefe Knoten. Jeder Ast wird individuell von Mensch oder KI entschieden; die Grenze von drei Ebenen gilt für das Backlog, nicht für die Tiefe in der Map. Die Vorschau zeigt nur, was die Struktur des Backlogs nicht erlaubt (Kriterium 3).
- Verworfen: Option A als Voreinstellung, weil die Tiefe nichts über die Ebene aussagt und Knoten wie ein späteres Epic zu Stichpunkten würden; Option B, weil sie den Menschen zum Umbau zwingt.

### Open

- Ob sich ein Ideen-Knoten auch zu einem Memo machen lässt (offen aus 2026-11-13).
- Wie die Vorschau je Knoten zwischen Parent-Child und Abhängigkeit wählen lässt (Folge aus 2026-11-23, Typwahl).
