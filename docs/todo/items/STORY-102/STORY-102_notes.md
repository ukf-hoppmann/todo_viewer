# STORY-102 — Freie Maps und Äste zwischen Bäumen umhängen und übertragen

## State

- Goal/Status: Geplant; zwei Tasks angelegt.
- Next step: Thema 6, Punkt 4 (entfernte Platzierungen merken?) entscheiden, dann Thema 7.
- Open:
  - Entfernte Platzierungen merken und wieder einsetzen (Aufwand mittel) oder weglassen; Entscheidung des Owners (2026-11-19)
  - Besprechung in Arbeit, Themenplan 2026-11-18, Themen 1 bis 5 erledigt, Thema 6 bis auf Punkt 4:  „Hier entfernen“ und „Knoten löschen“, 7 Summen und Zustand, 8 verbotene Fälle, 9 Markdown-Spiegel (2026-11-18)
- Decided:
  - „Hier entfernen“ / „Knoten löschen“: nur „Löschen“, wenn der Knoten in einem Baum steht; Rückfrage mit den Bäumen bei geteilten Knoten; letzte Platzierung weg heißt Papierkorb (auch für heimatlose Unterknoten); getrennt über API und MCP (2026-11-19)
  - Übertragene Äste: kleines Symbol mit Baumzahl beim Überfahren, das die Bäume des Knotens zum Springen anbietet; zusätzlich ein Schalter, der alle übertragenen Äste mit einem Rand einfärbt, damit man sie gezielt sehen kann und die Karte sonst ruhig bleibt (2026-11-19)
  - „Gehe hin“ zu einem Knoten in mehreren Bäumen: Auswahl des Baums; ebenso kann man aus einem Baum mit geteilten Knoten schnell in den anderen springen (2026-11-19)
  - Äste wandern nicht zwischen Projekten; Umhängen und Übertragen gelten nur innerhalb eines Projekts, die Gesamtansicht bleibt eine reine Ansicht (2026-11-19)
  - Umhängen und Übertragen gibt es auch über API und MCP, weil die KI Äste verschieben soll (2026-11-19)
  - Umhängen und Übertragen zwischen Bäumen: Kontextmenü „Umhängen nach …“ / „Übertragen nach …“ und Ziehen auf einen Eintrag der Map-Liste mit Auswahl „Umhängen oder Übertragen“; der Ast landet unter der Wurzel der Ziel-Map, die feine Position per Ziehen in der Ziel-Map; kein Zielknoten-Dialog (2026-11-19)
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

State confirmed after entry 2026-11-19 — Thema 6: „Hier entfernen“ und „Knoten löschen“ (a19e961ec692)

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

## 2026-11-19 — Thema 4: Bedienung von Umhängen und Übertragen

### Discussed

- Frage: Wie bedient man das Umhängen und Übertragen zwischen Bäumen? A: Kontextmenü am Knoten; B: Ziehen auf einen Eintrag der Map-Liste mit Menü „Umhängen oder Übertragen“; C: Zielknoten in einem Dialog wählen (genau, aber größter Aufwand). Empfehlung: A und B zusammen, C weglassen.
- Der Owner wendet ein, die Gesamtansicht mit künstlicher Wurzel, an der alle Bäume hängen, wäre ebenfalls ein Weg zum Ziehen. Einschätzung: Sie zeigt nach Thema 1 nur Projektbäume, keine freien Maps; für den Hauptfall (freie Map nach Projektbaum desselben Projekts) hilft sie daher nicht. Zwischen Projektbäumen verschiedener Projekte wäre sie möglich, aber der Code erlaubt das Verschieben bisher nur innerhalb eines Projekts (`dropPlacement`); ob Äste Projekte wechseln dürfen, ist offen.

### Decided

- A und B (Owner). Der Ast landet unter der Wurzel der Ziel-Map; Feinschliff per Ziehen in der Ziel-Map. C entfällt vorerst.

### Open

- Dürfen Äste zwischen Projekten wandern, und ist die Gesamtansicht dafür ein zusätzlicher Weg?

## 2026-11-19 — Thema 4: Projektgrenze und API

### Discussed

- Frage: Dürfen Äste zwischen Projekten wandern, und ist die Gesamtansicht dafür ein zusätzlicher Weg? Empfehlung: nein, weil Übergreifendes ohnehin nach „Allgemein“ gehört; die Gesamtansicht bleibt Ansicht.
- Der Owner stimmt zu und fordert: Umhängen und Übertragen müssen über eine API gehen, weil er viel an die KI auslagern will. Sein Wort „kopieren“ meint das Übertragen; Kopieren im Sinne einer eigenen Kopie gibt es weiterhin nicht (entschieden am 2026-11-13).

### Decided

- Nur innerhalb eines Projekts (Owner).
- API und MCP für Umhängen und Übertragen sind Teil der Story; in `TASK-063` als Kriterium aufgenommen (Owner).

### Open

- Thema 5: Markierung übertragener Äste und Pfad im Fokus.

## 2026-11-19 — Thema 5: Markierung übertragener Äste und Sprung

### Discussed

- Frage 1: Wie sieht die Markierung aus? Zur Wahl standen ein Symbol am Knoten (Empfehlung), ein farbiger Rand oder nur das Detail.
- Frage 2: Was gilt beim Sprung zu einem Knoten, der in mehreren Bäumen steht? Empfehlung war: Baum des Herkunftsorts, sonst die erste Platzierung, Wechsel über die Markierung.
- Der Owner kombiniert: Symbol nur beim Überfahren (Baum bleibt ruhig), dazu schaltbar ein farbiger Rand für alle übertragenen Äste, um sie gezielt zu finden. Beim Sprung soll er selbst den Baum wählen.

### Decided

- Symbol mit Baumzahl beim Überfahren plus schaltbarer Rand (Owner); das Symbol bietet die Bäume des Knotens zum Springen an.
- Sprung zu einem Knoten in mehreren Bäumen fragt per Auswahl nach dem Baum (Owner), statt eine Regel zu raten. Verworfen: feste Regel „erste Platzierung“, weil man sonst in einem unerwarteten Baum landet.

### Open

- Thema 6: „Hier entfernen“ und „Knoten löschen“.

## 2026-11-19 — Thema 6: „Hier entfernen“ und „Knoten löschen“

### Discussed

- Vorschläge: nur „Löschen“ bei Knoten in einem Baum; Rückfrage mit den Bäumen bei „Knoten löschen“ eines geteilten Knotens; verliert ein Knoten seine letzte Platzierung, kommt er mit den heimatlos gewordenen Unterknoten in den Papierkorb; Items nach der Regel von `STORY-100`; „Hier entfernen“ ohne Rückfrage; getrennte Namen in API und MCP. Der Owner stimmt zu, mit Ausnahme von Punkt 4.
- Punkt 4 (Wiederherstellen von „Hier entfernen“): Der Papierkorb kennt Knoten, keine Platzierungen. Der Owner möchte wissen, wie viel Arbeit es ist, die Orte zu merken, an denen der Knoten stand, weil man sonst ein versehentliches Entfernen nicht wirklich rückgängig machen kann und sich den Ort merken muss.
- Aufwand (Einschätzung am Code: `mindmap_placements` mit Schlüssel (Baum, Knoten), Papierkorb über `workspace`): Option 1, Platzierung nur als entfernt markieren statt löschen (neue Spalte, Migration v4); alle Abfragen, Summen und die Regel „höchstens einmal je Baum“ müssen markierte Zeilen ausnehmen; Wiederherstellen braucht Regeln, wenn Parent oder Platz inzwischen fehlt oder der Knoten dort schon wieder steht; ein Ast wird als Gruppe entfernt und zurückgeholt; API, MCP und eine Stelle in der Oberfläche („Früher in …“ am Knoten mit „Wieder einsetzen“); mittlerer Aufwand, etwa ein eigener Task. Option 2, nur „Rückgängig“ direkt nach der Aktion: klein, hilft aber nicht später. Option 3, weglassen: kein Aufwand, der Ast ist über den anderen Baum wieder erreichbar.

### Decided

- Punkte 1, 2, 3 und 5 wie vorgeschlagen (Owner); in `TASK-063` und im Konzept eingetragen.

### Open

- Punkt 4: Entscheidung zwischen Option 1, 2 und 3; Empfehlung: Option 1 als eigener Task nach `TASK-063`, damit dieser klein bleibt.
