# STORY-105 — Mindmap im Markdown-Spiegel: Dateiformat und Sync

## State

- Goal/Status: Geplant und in Tasks geschnitten; die Specs der Tasks sind geschrieben; nicht Pflicht für das Epic.
- Next step: Tasks nach der ersten lauffähigen Fassung der Mindmap in der Reihenfolge ihrer Abhängigkeiten umsetzen; erste Task ist `NEW-mirror-format`.
- Open:
  - Nichts offen für die Planung (2026-11-23)
- Decided:
  - Anforderungen aus `STORY-102`: mehrere Maps je Projekt mit Name und Art; mehrfache Platzierungen je Knoten bei einmaligem Inhalt; entfernte Platzierungen (`TASK-066`) und Papierkorb erkennbar; eine Cloud-Sitzung füllt freie Maps und hängt Äste um oder überträgt sie mit denselben Regeln wie die API (2026-11-19)
  - Der Spiegel wird mitgeplant; wenn er umsetzbar ist, wird er gebaut, sonst entfällt er, der Owner hätte ihn lieber (2026-11-13)
  - Gebaut wird er erst nach der ersten lauffähigen Fassung der Mindmap (2026-11-13)
  - Dateiformat: Jeder Knoten steht einmal mit Inhalt und Label in einer Datei; jeder Baum (Projektbaum oder freie Map) ist eine eigene Datei, die nur Labels in ihrer Ordnung auflistet; mehrfache Platzierungen sind Verweise, der Inhalt steht nie doppelt (2026-11-23)
  - Kriterium 3 ist angepasst: Die Regeln für den Datei-Modus sind beschrieben, und der Owner hat einen fertigen Prompt für Claude_Harness; die KI übergibt nicht selbst (2026-11-23)
  - Zuschnitt in vier Tasks: Format und Codec, Teilnehmer für Knoten und Bäume, Zuordnungen mit Dokumenten und Papierkorb, Abschluss mit Sync-Dialog, Cloud-Test, Doku und Prompt (2026-11-23)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`; Tasks `NEW-mirror-format`, `NEW-mirror-participant-core`, `NEW-mirror-participant-links`, `NEW-mirror-finish`

State confirmed after entry 2026-11-23 — Zuschnitt in Tasks (c16e5b424004)

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

## 2026-11-23 — Kriterium 3: Prompt statt Übergabe

### Discussed

- Wie bei `STORY-104` übergibt die KI die Regeln nicht selbst an Claude_Harness. Der Owner hat der Anpassung zugestimmt.

### Decided

- Kriterium 3 lautet: Die Regeln für den Datei-Modus sind beschrieben, und der Owner hat einen fertigen Prompt für Claude_Harness.

### Open

- Nichts.

## 2026-11-23 — Zuschnitt in Tasks

### Discussed

- Die Story folgt dem Muster des Memos-Spiegels (Syntax, Encode, Decode, Codec, Teilnehmer) und ist nach Schichten der Reihe nach schneidbar: erst Format und Codec ohne Datenbank, dann der Teilnehmer in zwei Stufen, dann der Abschluss.
- Die Zuordnung steht auf dem Knoten, nicht im Item, weil die Dateien der Items dem Harness gehören.

### Decided

- Vier Tasks mit Specs und Notes angelegt; das Format ist in der Spec der ersten Task festgelegt (Dateien, Kopfzeilen, Verweise, Platzhalter)
- Eigene Versionszählung (Version 1) für das Mindmap-Format, unabhängig vom Backlog-Format

### Open

- Nichts offen für die Planung.
