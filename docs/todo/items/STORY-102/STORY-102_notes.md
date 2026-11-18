# STORY-102 — Freie Maps und Äste zwischen Bäumen umhängen und übertragen

## State

- Goal/Status: Geplant; zwei Tasks angelegt.
- Next step: Thema 4 (Bedienung von Umhängen und Übertragen) besprechen.
- Open:
  - Besprechung in Arbeit, Themenplan 2026-11-18, Themen 1 bis 3 erledigt: 4 Bedienung Umhängen/Übertragen, 5 Markierung und Pfad im Fokus, 6 „Hier entfernen“ und „Knoten löschen“, 7 Summen und Zustand, 8 verbotene Fälle, 9 Markdown-Spiegel (2026-11-18)
- Decided:
  - Freie Map löschen: Papierkorb mit Wiederherstellen; Knoten nur dieser Map gehen mit, übertragene Äste bleiben im anderen Baum, Items fallen an den Parent-Knoten oder in „Nicht zugeordnet“; der Projektbaum lässt sich nicht löschen (2026-11-18)
  - Die Maps eines Projekts stehen als Liste in der Seitenleiste (Projektbaum zuerst, dann freie Maps; Anlegen, Umbenennen, Löschen dort) (2026-11-18)
  - Die Gesamtansicht zeigt nur Projektbäume; freie Maps stehen dort nicht (2026-11-18)
  - Projektbaum und freie Maps werden gemischt, damit man flexibel gestalten kann (2026-11-13)
  - Freie Maps gehören zu einem Projekt; Übergreifendes kommt ins eingebaute Projekt „Allgemein“ (2026-11-13)
  - Keine eigene Map je Memo; ein Memo wird an einen Knoten oder eine freie Map verlinkt. Cloud-Zugriff auf freie Maps über den Spiegel `STORY-105` (2026-11-18)
  - „Export nach Memo“ (Baum als Liste ins Memo) wird nicht gebaut, sondern als Memo mit Prüfdatum 2027-02-18 festgehalten (2026-11-18)
  - Nichts wird kopiert; es gibt „umhängen“ (aus A weg, in B drin) und „übertragen“ (derselbe Ast in A und B) (2026-11-13)
  - Übertragen geht nur zwischen Bäumen; innerhalb eines Baums gibt es nur Umhängen (2026-11-13)
  - Platzierungen sind gleichberechtigt: Wird der Ast aus einem Baum entfernt, bleibt er im anderen vollwertig (2026-11-13)
  - Verworfen: Verweis-Knoten auf ein Original, weil der Verweis ins Leere zeigt, sobald das Original entfernt wird (2026-11-13)
  - Ein übertragener Ast ist ein gemeinsamer Knoten und überall gleich; ein „Trennen“ in eine eigenständige Kopie gibt es vorerst nicht, bei Bedarf wird umgebaut (2026-11-13)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`

State confirmed after entry 2026-11-18 — Thema 3: Löschen freier Maps (ff718591cd19)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `TASK-064`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.
- Folgen des Übertragens: Summen ohne Doppelzählung, zwei Aktionen zum Entfernen, im Fokus folgt der Pfad dem Weg, über den man kam, übertragene Äste sind markiert.

### Decided

- Projektbaum und freie Maps werden gemischt, damit man flexibel gestalten kann
- Freie Maps gehören zu einem Projekt; Übergreifendes kommt ins eingebaute Projekt „Allgemein“
- Die Mindmap zu einem Memo lebt allein in diesem Memo
- Nichts wird kopiert; es gibt „umhängen“ (aus A weg, in B drin) und „übertragen“ (derselbe Ast in A und B)
- Übertragen geht nur zwischen Bäumen; innerhalb eines Baums gibt es nur Umhängen
- Platzierungen sind gleichberechtigt: Wird der Ast aus einem Baum entfernt, bleibt er im anderen vollwertig
- Verworfen: Verweis-Knoten auf ein Original, weil der Verweis ins Leere zeigt, sobald das Original entfernt wird

### Open

- Der Owner erwartet, dass sich übertragene Äste in beiden Bäumen unterschiedlich entwickeln können. Mit einem gemeinsamen Knoten ist der Ast aber überall derselbe; getrennte Entwicklung hieße trennen, also doch kopieren. Rückfrage gestellt
- Wo man zwischen Projektbaum und freien Maps wählt, hängt am Aufbau der Mindmap-Seite

## 2026-11-13 — Übertragene Äste bleiben gemeinsam

### Discussed

- Open vom 2026-11-13 (getrennte Entwicklung übertragener Äste) geklärt. Zur Wahl standen: gemeinsam (ein Ast, überall gleich) oder zusätzlich eine Aktion „trennen“, die eine eigenständige Kopie erzeugt.

### Decided

- Start mit „gemeinsam“; wenn sich zeigt, dass getrennte Entwicklung gebraucht wird, wird umgebaut (Owner).

### Open

- Wo man zwischen Projektbaum und freien Maps wählt, hängt weiter am Aufbau der Mindmap-Seite.

## 2026-11-18 — Themenplan der Besprechung

### Discussed

- Vor der Umsetzung von `TASK-062` und `TASK-063` werden offene Punkte der Reihe nach geklärt. Die Abhängigkeiten `STORY-099` und `STORY-100` sind abgeschlossen; `STORY-101` wartet auf Bestätigung.
- Themen: 1 Auswahl zwischen Projektbaum und freien Maps (blockiert `TASK-062`), 2 Map eines Memos, 3 Löschen freier Maps, 4 Bedienung von Umhängen und Übertragen, 5 Markierung übertragener Äste und Pfad im Fokus, 6 „Hier entfernen“ und „Knoten löschen“, 7 Summen und Zustand bei übertragenen Ästen, 8 verbotene Fälle (Kreise, Knoten schon im Zielbaum), 9 Folgen für den Markdown-Spiegel `STORY-105`.

### Open

- Alle neun Themen; Reihenfolge wie oben.

## 2026-11-18 — Thema 1: Auswahl der Maps

### Discussed

- Frage: Wie wählt man zwischen Projektbaum und freien Maps, und was zeigt die Gesamtansicht? Mockup mit den drei Varianten: https://claude.ai/artifact/3qoj9AET4gmLVxg4Nx8gGw
- A, Map-Liste in der Seitenleiste: Verwalten und Auswählen an festem Ort, beim Umhängen und Übertragen sind die Ziele sichtbar; die Seitenleiste wird länger. Empfehlung.
- B, Tabs über der Karte: schneller Wechsel, aber bei vielen Maps unübersichtlich; Verwalten braucht ein zusätzliches Menü.
- C, Dropdown im Kopf der Karte: platzsparend, aber die Maps sind versteckt.
- Gesamtansicht: nur Projektbäume (übersichtlich) oder auch freie Maps als zusätzliche Äste (erzeugt Doppelungen bei übertragenen Ästen). Empfehlung: nur Projektbäume.

### Decided

- Variante A: Map-Liste in der Seitenleiste (Owner).
- Freie Maps stehen in der Gesamtansicht nicht; sie zeigt nur Projektbäume (Owner).
- Verworfen: B (Verwalten braucht Zusatzmenü, unübersichtlich bei vielen Maps) und C (Maps versteckt), außerdem freie Maps als Äste der Gesamtansicht (Doppelungen).

### Open

- Thema 2: Map eines Memos.

## 2026-11-18 — Thema 2: Map eines Memos, Klarstellung

### Discussed

- Der Owner präzisiert „lebt allein im Memo“: gemeint ist eine Brainstorming-Map, die nicht irgendwo in der Mindmap-Datenbank liegt, sondern im Memo gespeichert wird, damit eine Cloud-Sitzung sie füllen kann. Die Cloud-Begründung stand bisher nirgends in den Notes; in `TASK-064` stand nur „die Map eines Memos lebt in dem Memo“ und „speist sich nur aus dem einen Memo“.
- Reine Brainstorming-Maps ohne Memo gibt es mit den freien Maps. Deren Cloud-Zugriff hängt am Markdown-Spiegel `STORY-105`; Memos sind schon Dateien im Spiegel.
- Option 1, Map im Memo gespeichert: Cloud-Sitzung füllt sie über die Memo-Datei; aber ein zweites Speichermodell neben den Mindmap-Tabellen, und Umhängen oder Übertragen in andere Bäume (diese Story) wird schwierig, weil der Knoten dann in einer Memo-Datei liegt.
- Option 2, freie Map plus Verknüpfung zum Memo: ein Modell, Umhängen und Übertragen funktionieren; Cloud-Zugriff kommt mit `STORY-105`. Empfehlung.

### Open

- Entscheidung des Owners zwischen Option 1 und 2; bei Option 2 entfallen die Map-eines-Memos-Teile in `TASK-062` und im Epic-Konzept.

## 2026-11-18 — Thema 2: Export oder Sync einer freien Map in ein Memo

### Discussed

- Neue Idee des Owners: Brainstorming in einer freien Map; die Einträge werden als Aufzählungspunkte in einem Memo abgelegt, damit die Ergebnisse systematisch nachlesbar sind. Als „Export nach Memo“ oder „Sync nach Memo“, wobei der Baum mit dem Memo verknüpft ist, das die Liste trägt. Der Owner fragt nach dem Aufwand und ob der Nutzen ihn jetzt rechtfertigt oder ob man es bei Bedarf nachzieht.
- Das Memo hat ein Textfeld (`body`); ein Export schreibt den Baum als verschachtelte Liste dorthin.
- Option 1, einmaliger Export (Baum zu Markdown-Liste im Memo): klein; eine Funktion, ein Endpunkt, ein Knopf, dazu die Verknüpfung Baum–Memo. Eine erneute Ausführung ersetzt die Liste. Wegen der gemeinsamen Äste gibt es dabei Doppelungen, die man festlegen muss.
- Option 2, Sync in eine Richtung (Baum ändert Memo bei jeder Änderung): braucht Auslöser und Regeln, was bei von Hand geänderten Memos gilt; mittel.
- Option 3, Sync in beide Richtungen: Liste lesen, Knoten zuordnen, Verschieben, Löschen und Konflikte, dazu gemeinsame Äste; groß und fehleranfällig.
- Einschätzung: Nutzen ungewiss, Cloud-Zugriff kommt ohnehin mit dem Markdown-Spiegel `STORY-105`. Option 1 lässt sich später ohne Umbau nachziehen, weil sie nur liest.

### Open

- Entscheidung des Owners: Memo-Map ganz streichen und Export nach Memo erst bei Bedarf? Empfehlung: ja, als Idee in einem Memo oder Item festhalten.

## 2026-11-18 — Thema 2: Entscheidung und Umsetzung in der Planung

### Decided

- Memo-Map gestrichen; freie Maps bleiben, ein Memo wird daran verlinkt wie an einen Knoten (Owner, Empfehlung angenommen). Grund: ein Speichermodell weniger, Umhängen und Übertragen bleiben einfach, Cloud-Zugriff kommt mit dem Spiegel.
- „Export nach Memo“ wird erst bei Bedarf gebaut; als Memo mit Prüfdatum festgehalten (Owner).
- `STORY-105` muss freie Maps enthalten, damit eine Cloud-Sitzung sie füllen kann (Owner).

### Discussed

- Angepasst: Ziel und Kriterien von `STORY-102` und `TASK-062` (Titel ohne Memo-Map, Maps-Liste in der Seitenleiste), Kriterium 1 von `STORY-105`, Konzept `EPIC-008_spec.md` (Begriffe, Darstellung, Spiegel, Idee Export). Das Memo `MEMO-003` hält die Export-Idee fest.

### Open

- Thema 3: Löschen freier Maps.

## 2026-11-18 — Thema 3: Löschen freier Maps

### Discussed

- Frage: Was geschieht beim Löschen einer ganzen freien Map? Zur Wahl standen Papierkorb mit Wiederherstellen (wie bei Knoten, `STORY-099`) oder sofortiges Löschen mit Rückfrage. Empfehlung: Papierkorb.
- Folgen: Knoten, die nur in dieser Map stehen, gehen mit; übertragene Äste verlieren nur die Platzierung in dieser Map und bleiben im anderen Baum (folgt aus gleichberechtigten Platzierungen); die Rückfrage nennt, wie viele Äste anderswo erhalten bleiben; Items an gelöschten Knoten fallen an den Parent-Knoten, sonst nach „Nicht zugeordnet“ (Regel aus `STORY-100`).

### Decided

- Papierkorb mit Wiederherstellen; Knoten nur dieser Map gehen mit, übertragene Äste bleiben im anderen Baum, Items wie bei gelöschten Knoten; der Projektbaum lässt sich nicht löschen (Owner).

### Open

- Thema 4: Bedienung von Umhängen und Übertragen.
