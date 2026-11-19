# STORY-105 — Mindmap im Markdown-Spiegel: Dateiformat und Sync

## State

- Goal/Status: Geplant; nicht Pflicht für das Epic.
- Next step: Nach der ersten lauffähigen Fassung prüfen, ob das Format umsetzbar ist; Anforderungen aus `STORY-102` beachten.
- Open:
  - Wie Platzierungen eines Astes in mehreren Bäumen in Dateien stehen, ohne dass der Ast doppelt geschrieben wird (2026-11-13)
- Decided:
  - Anforderungen aus `STORY-102`: mehrere Maps je Projekt mit Name und Art; mehrfache Platzierungen je Knoten bei einmaligem Inhalt; entfernte Platzierungen (`TASK-066`) und Papierkorb erkennbar; eine Cloud-Sitzung füllt freie Maps und hängt Äste um oder überträgt sie mit denselben Regeln wie die API (2026-11-19)
  - Der Spiegel wird mitgeplant; wenn er umsetzbar ist, wird er gebaut, sonst entfällt er, der Owner hätte ihn lieber (2026-11-13)
  - Gebaut wird er erst nach der ersten lauffähigen Fassung der Mindmap (2026-11-13)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`

State confirmed after entry 2026-11-19 — Anforderungen aus STORY-102 (e18877ce9a6d)

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
