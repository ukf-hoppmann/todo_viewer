# TASK-066 — Mindmap: entfernte Platzierungen merken und wieder einsetzen

## State

- Goal/Status: Geplant; Entscheidung aus der Besprechung von `STORY-102` übernommen, nicht Pflicht für die Story.
- Next step: Nach `TASK-063` beginnen; Plan beim Start vorstellen.
- Open:
  - Ersatzregel beim Wiedereinsetzen, wenn Parent oder Platz fehlt (Vorschlag: unter die Wurzel der Map) (Details beim Start) (2026-11-19)
  - Der Knoten kann inzwischen wieder im Baum stehen; Wiedereinsetzen muss das prüfen (Hinweis aus Thema 8) (2026-11-19)
- Decided:
  - Entfernte Platzierungen werden gemerkt statt gelöscht und lassen sich wieder einsetzen (Weg 1) (2026-11-19)
  - Ein Ast wird als Gruppe entfernt und kommt als Gruppe zurück (2026-11-19)
- References: Spec `TASK-066_spec.md`; Story-Spec `STORY-102_spec.md`; Vorgänger `TASK-063`

State confirmed after entry 2026-11-19 — Übernahme der Entscheidungen aus STORY-102 (e5bb8fa6de78)

## 2026-11-19 — Übernahme der Entscheidungen aus STORY-102

### Discussed

- Frage: Wie macht man „Hier entfernen“ rückgängig? Der Papierkorb kennt Knoten, keine Platzierungen, und der Owner möchte den Ort nicht im Kopf behalten müssen.
- Weg 1: Platzierung nur als entfernt markieren (neue Spalte, Migration v4). Abfragen, Summen und die Regel „höchstens einmal je Baum“ nehmen markierte Zeilen aus. Wiederherstellen braucht Regeln, wenn Parent oder Platz fehlt oder der Knoten dort schon steht; ein Ast kommt als Gruppe zurück; API, MCP und eine Stelle am Knoten („Früher in …“). Aufwand mittel, Einschätzung am Code ohne Messung.
- Weg 2: nur „Rückgängig“ direkt danach: klein, hilft später nicht. Weg 3: weglassen: kein Aufwand, die alte Position ginge verloren.

### Decided

- Weg 1, als eigener Task nach `TASK-063`, damit dieser klein bleibt; nicht Pflicht für die Story (Owner). Verworfen: Weg 2 (hilft später nicht) und Weg 3 (alte Position verloren).

### Open

- Ersatzregel beim Wiedereinsetzen; Prüfung, ob der Knoten inzwischen im Baum steht.
