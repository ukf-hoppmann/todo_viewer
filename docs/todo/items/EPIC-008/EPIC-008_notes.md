# EPIC-008 — Mindmap: Themen-Gerippe zum Brainstormen und als Übersicht des Backlogs

## State

- Goal/Status: Stories 099 bis 102 sind abgeschlossen; die offenen Stories 103 bis 106 sind durchgeplant und in 15 Tasks mit Specs geschnitten.
- Next step: Umsetzung der 15 Tasks in Wellen (siehe Eintrag 2026-11-23 „Umsetzungsplan“); je Task eine eigene Session auf eigenem `claude/…`-Branch, Tasks einer Welle laufen parallel; Welle 1: `TASK-069`, `TASK-068`, `TASK-079` (2026-11-23)
- Open:
  - Nichts offen für die Planung (2026-11-23)
- Decided:
  - Die Mindmap ist ein eigenes Datenmodell und nur ein Gerippe; sie verlinkt Items und Memos, ähnlich dem Feld Area, und kopiert nichts (2026-11-13)
  - Es gibt nur ein Modell: Ob ein Knoten bloße Idee oder schon im Backlog ist, ergibt sich aus dem, was daran hängt (2026-11-13)
  - Kernanforderung ist die Übersicht: mit wenigen Schritten sehen, was es gibt und was kommt; Items sind deshalb nie eigene Knoten (2026-11-13)
  - Topics der Memos bleiben unverändert und gehören nicht in die Mindmap (2026-11-13)
  - Der Viewer bekommt keine eigene LLM-Anbindung; die KI arbeitet über API und MCP (2026-11-13)
  - Die Umsetzung läuft in einem eigenen neuen Branch, weil es ein großer experimenteller Umbau ist, und in vielen kleinen Schritten (2026-11-13)
  - Der Markdown-Spiegel wird mitgeplant und ist für das Epic nicht Pflicht (2026-11-13)
  - Der Seitenaufbau folgt zunächst dem Backlog (Sidebar, Baum, Detailspalte); die Detailspalte ist schließbar; spätere Anpassung ist möglich (2026-11-16)
  - Die Mindmap ersetzt das Feld Area (2026-11-16)
  - Der Branch heißt `todo_mindmap`, zweigt von `main` ab und enthält die Planung per Merge aus `claude/nice-volta-6mvn99` (2026-11-16)
  - Jeder Task läuft in eigener Session auf eigenem `claude/…`-Branch und wird nach `todo_mindmap` gemergt; Plan für `STORY-099` freigegeben (2026-11-16)
  - Auf `todo_mindmap` gibt es keine Releases (kein Versionsschritt nach den Merges der Tasks); die Version wird erst mit der Rückführung geklärt (2026-11-16)
  - Reihenfolge der Umsetzung: `STORY-106`, `STORY-103`, `STORY-104`, zuletzt `STORY-105`; `STORY-106` läuft zuerst, weil danach das Anlegen aus einem Knoten kein Area mehr verlangt (2026-11-23)
  - Überführen ins Backlog: kein Automatismus nach Ebene oder Tiefe, Item oder Memo je Knoten (`STORY-103`) (2026-11-23)
  - Die Regel für die KI steht in den MCP-Tool-Beschreibungen; Claude_Harness bekommt einen Prompt, den der Owner selbst übergibt (`STORY-104`) (2026-11-23)
  - Spiegel: Inhalt einmal je Knoten, Bäume als Verweise (`STORY-105`) (2026-11-23)
  - Area entfällt ganz, Backlog-Format Version 3; der Themenbaum entsteht durch eine KI mit Prompt für den Owner (`STORY-106`) (2026-11-23)
  - Die Berichtigung von Kriterium 1 in `STORY-106` (kein Filter nach Thema, Anzeige im Abschnitt „Knoten“) ist bestätigt (2026-11-23)
- References: Spec `EPIC-008_spec.md`; Ideensammlung `TASK-064`; Stories `STORY-099`, `STORY-100`, `STORY-101`, `STORY-102`, `STORY-103`, `STORY-104`, `STORY-105`

State confirmed after entry 2026-11-23 — Umsetzungsplan: Wellen für parallele Sessions (e5c3e1e9e41f)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `TASK-064`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.

### Decided

- Die Mindmap ist ein eigenes Datenmodell und nur ein Gerippe; sie verlinkt Items und Memos, ähnlich dem Feld Area, und kopiert nichts
- Es gibt nur ein Modell: Ob ein Knoten bloße Idee oder schon im Backlog ist, ergibt sich aus dem, was daran hängt
- Kernanforderung ist die Übersicht: mit wenigen Schritten sehen, was es gibt und was kommt; Items sind deshalb nie eigene Knoten
- Topics der Memos bleiben unverändert und gehören nicht in die Mindmap
- Der Viewer bekommt keine eigene LLM-Anbindung; die KI arbeitet über API und MCP
- Die Umsetzung läuft in einem eigenen neuen Branch, weil es ein großer experimenteller Umbau ist, und in vielen kleinen Schritten
- Der Markdown-Spiegel wird mitgeplant und ist für das Epic nicht Pflicht

### Open

- Genauer Aufbau der Mindmap-Seite (Auswahl der Maps, Schalter für Ansicht und Anordnung); der Owner will ihn noch klären
- Ob das Feld Area neben der Mindmap bestehen bleibt
- Von welchem Stand der neue Branch abzweigt und wann er zurückgeführt wird

## 2026-11-16 — Seitenaufbau, Area, Branch

### Discussed

- Seitenaufbau: A (Sidebar, Baum, Detailspalte wie im Backlog), B (Mindmap vorn, Detail schwebend), C (Reiter für Maps). A passt zum vorhandenen Seitengerüst (`STORY-088`) und ist am wenigsten Aufwand.
- Area: daneben lassen (doppelte Einordnung) oder ersetzen bzw. ableiten (sauberer, späterer Umbau).
- Branch: `main` enthielt die Planung von Epic 8 nicht; sie lag nur auf `claude/nice-volta-6mvn99`.

### Decided

- Seitenaufbau zunächst wie im Backlog (Variante A); die Detailspalte ist schließbar; spätere Anpassung ist möglich
- Die Mindmap ersetzt das Feld Area
- Branch `todo_mindmap`, von `main` abgezweigt, Planung per Merge hereingeholt; main ist danach in ihm enthalten und ist der Ausgangspunkt

### Open

- Open from 2026-11-13 (Aufbau der Mindmap-Seite, Area, Branch) resolved: siehe oben
- Wie Area ersetzt wird und wann (eigene Story, vom Owner freizugeben)

## 2026-11-16 — Umsetzungsplan freigegeben, Sessions

### Discussed

- Plan für `STORY-099`: Server-Plugin `mindmap` (`TASK-052`), Seite (`TASK-053`), Ziehen (`TASK-054`), Notizen (`TASK-055`); die Tasks bauen aufeinander auf.
- Wo die Sessions arbeiten: eigene `claude/…`-Branches oder direkt auf `todo_mindmap`.

### Decided

- Der Umsetzungsplan für `STORY-099` ist vom Owner freigegeben
- Jeder Task läuft in einer eigenen neuen Session auf einem eigenen `claude/…`-Branch; gemergt wird immer nach `todo_mindmap`
- Die Tasks laufen nacheinander; die nächste Session startet erst, wenn die vorige gemergt ist

### Open

- Wo die Dokument-Logik für Knoten liegt (gemeinsamer Baustein im Workspace oder `requires: backlog`): vor `TASK-055` klären

## 2026-11-16 — Kein Release auf dem Mindmap-Branch

### Discussed

- Die Versionsregel sieht nach jedem Merge einer Änderung einen Versionsschritt vor; nach `TASK-053` wäre es 0.11.0 gewesen. `todo_mindmap` ist ein Experimentier-Branch, nach `TASK-052` gab es ebenfalls keinen Schritt.

### Decided

- Der Owner entscheidet: kein Release auf `todo_mindmap`

## 2026-11-23 — Planung der offenen Stories

### Discussed

- Die Stories `STORY-103` bis `STORY-106` wurden der Reihe nach mit dem Owner durchgesprochen (Optionen, Gründe und verworfene Wege stehen in den Notes der Stories) und in Tasks geschnitten.
- Beim Zuschnitt zeigte sich, dass `STORY-106` zuerst laufen muss, und dass das Dateiformat des Backlogs Claude_Harness gehört (Version 3).

### Decided

- Siehe die Entscheidungen im Kopf; Ausführung in der genannten Reihenfolge.

### Open

- Der Owner bestätigt bei der Abnahme die Beziehungswahl im Ast-Dialog (`TASK-076`) und die Berichtigung von Kriterium 1 in `STORY-106`.

## 2026-11-23 — Berichtigung von Kriterium 1 bestätigt

### Discussed

- Der Owner hat die Berichtigung geprüft.

### Decided

- Kriterium 1 von `STORY-106` bleibt wie berichtigt.

### Open

- Nichts.

## 2026-11-23 — Umsetzungsplan: Wellen für parallele Sessions

### Discussed

- Ziel: die 15 offenen Tasks in jeweils eigener, neuer Session abarbeiten, so parallel wie die Abhängigkeiten es erlauben. Grundlage sind die Felder `Dependencies` der Tasks.
- Die frühere Reihenfolge (`STORY-106`, `103`, `104`, zuletzt `105`) bleibt für die Hauptlinie; der Spiegel (`STORY-105`) hängt nur an `STORY-100` und `STORY-102` (beide abgeschlossen) und kann deshalb als zweite Spur nebenher laufen. Risiko: Merge-Konflikte an gemeinsamen Dateien; die Spiegel-Tasks berühren Area nicht.

### Decided

- Welle 1 (parallel): `TASK-069`, `TASK-068`, `TASK-079`.
- Welle 2: `TASK-070` (nach `TASK-069`), `TASK-080` (nach `TASK-079`).
- Welle 3: `TASK-071` (nach `TASK-068` und `TASK-070`), `TASK-081` (nach `TASK-080`).
- Welle 4: `TASK-072` und `TASK-073` (beide nach `TASK-071`), `TASK-082` (nach `TASK-081`).
- Welle 5: `TASK-075`, `TASK-074`, `TASK-077` (alle nach `TASK-073`).
- Welle 6: `TASK-076` (nach `TASK-074` und `TASK-075`), `TASK-078` (nach `TASK-077`).
- Jede Session: Task auf `In progress`, Plan nach `harness-decomposition`, Umsetzung auf eigenem `claude/…`-Branch, danach `Awaiting confirmation`; gemergt wird nach `main`, die nächste Welle startet erst nach dem Merge der Vorgänger.

### Open

- Der Owner bestätigt Start von Welle 1 und die zweite Spur für `STORY-105`.

