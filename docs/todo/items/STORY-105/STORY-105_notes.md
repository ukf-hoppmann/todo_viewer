# STORY-105 — Mindmap im Markdown-Spiegel: Dateiformat und Sync

## State

- Goal/Status: Geplant; nicht Pflicht für das Epic; Grundform des Dateiformats entschieden.
- Next step: Nach der ersten lauffähigen Fassung prüfen, ob das Format umsetzbar ist; Anforderungen aus `STORY-102` beachten.
- Open:
- Decided:
  - Anforderungen aus `STORY-102`: mehrere Maps je Projekt mit Name und Art; mehrfache Platzierungen je Knoten bei einmaligem Inhalt; entfernte Platzierungen (`TASK-066`) und Papierkorb erkennbar; eine Cloud-Sitzung füllt freie Maps und hängt Äste um oder überträgt sie mit denselben Regeln wie die API (2026-11-19)
  - Der Spiegel wird mitgeplant; wenn er umsetzbar ist, wird er gebaut, sonst entfällt er, der Owner hätte ihn lieber (2026-11-13)
  - Gebaut wird er erst nach der ersten lauffähigen Fassung der Mindmap (2026-11-13)
  - Dateiformat: Jeder Knoten steht einmal mit Inhalt und Label in einer Datei; jeder Baum (Projektbaum oder freie Map) ist eine eigene Datei, die nur Labels in ihrer Ordnung auflistet; mehrfache Platzierungen sind Verweise, der Inhalt steht nie doppelt (2026-11-23)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`

State confirmed after entry 2026-11-23 — Platzierungen in Dateien (7ad2f23da401)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `TASK-064`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.
- Grund: Cloud-Sitzungen arbeiten nur auf den Dateien; ohne Format kann die KI dort Items nicht zuordnen.

### Decided

- Der Spiegel wird mitgeplant; wenn er umsetzbar ist, wird er gebaut, sonst entfällt er, der Owner hätte ihn lieber
- Gebaut wird er erst nach der ersten lauffähigen Fassung der Mindmap

### Open

- Wie Platzierungen eines Astes in mehreren Bäumen in Dateien stehen, ohne dass der Ast doppelt geschrieben wird

## 2026-11-19 — Anforderungen aus STORY-102

### Decided

- Das Dateiformat muss abbilden: mehrere Bäume je Projekt (Projektbaum und freie Maps, mit Name und Art), mehrfache Platzierungen je Knoten mit je Baum eigenem Parent und eigener Stelle bei einmaligem Inhalt, entfernte Platzierungen aus `TASK-066`, Papierkorb mit Platzierungen. Eine Cloud-Sitzung muss freie Maps füllen und Äste umhängen oder übertragen können und dabei dieselben Regeln einhalten wie die API (keine Kreise, kein Knoten doppelt im Baum, nur im selben Projekt) (Owner). Kriterium 1 von `STORY-105` ist entsprechend ergänzt.

### Open

- Die genaue Form des Formats bleibt offen (siehe Kopf).

## 2026-11-23 — Platzierungen in Dateien

### Discussed

- Frage: Wie stehen mehrfache Platzierungen eines Astes in Dateien, ohne dass der Ast doppelt geschrieben wird?
- Option A: Inhalt einmal je Knoten, Bäume als eigene Dateien mit Verweisen auf Labels. Eine Wahrheit je Knoten, Umhängen ändert nur die Baumdatei; ein Baum ist nicht als zusammenhängender Text lesbar.
- Option B: Ast in jedem Baum ausschreiben. Gut lesbar, aber der Inhalt steht doppelt und kann beim Sync auseinanderlaufen.
- Option C: ein Besitzer-Baum mit dem ausgeschriebenen Ast, die anderen mit Verweis. Lesbar, aber Umhängen und Löschen machen den Besitzer heikel.
- Empfehlung war A: passt zum Prinzip, dass nichts kopiert wird, und ist bei Cloud-Sitzungen einfach, weil sie nur Baumdateien ändern.

### Decided

- Option A.
- Verworfen: B wegen doppeltem Inhalt und Sync-Konflikten; C wegen des Besitzers beim Umhängen und Löschen.

### Open

- Nichts offen für die Planung; die Story entfällt oder wird gebaut nach der ersten lauffähigen Fassung (entschieden am 2026-11-13).
