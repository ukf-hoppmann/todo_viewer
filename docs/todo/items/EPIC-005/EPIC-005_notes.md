# EPIC-005 — Notizen und Wiedervorlage: Topics, Notes, Auslöser

## 2026-10-08 — Klärung vor Umsetzung: Grundsätze, Datenmodell, Auslöser

### Discussed

- Reihenfolge der Stories
- Rolle von Markdown für Notes
- Label-Vergabe, Topic-Tiefe, Projektwechsel, Auslöser-Logik
- Prüfung der Auslöser ohne Hintergrund-Takt

### Decided

- Reihenfolge: STORY-037, 038, 039, 040, 043, 045 (erster nutzbarer Schnitt), dann 042, 041, 044, 047, 046.
- Die API ist die Hauptanwendung für Notes. Markdown ist nur Export/Import bzw. Sync-Option (STORY-047), kein Normalbetrieb. Der Besitzer will Markdown auch für das Backlog im Normalgebrauch abschaffen; das ist nicht Teil von EPIC-005.
- Labels NOTE-001/TOPIC-001 zählen pro Projekt und Typ wie bei Epic/Story/Task; Links zeigen auf die interne uid.
- Topic-Tiefe 3 als Standard, konfigurierbar.
- Eine Note darf das Projekt wechseln und bekommt dann ein passendes Label des Zielprojekts.
- Mehrere Auslöser pro Note (Zeitpunkt und Ereignis, z. B. 11.12.2027 9 Uhr und nach Abschluss von TASK-007). Jeder Auslöser reagiert einzeln; zusätzlich wird erkannt, wenn alle eingetroffen sind. Das Modell hat einen Modus 'any'/'all' für einen späteren Schalter.
- Zeitzone ist die des Rechners, auf dem der Viewer läuft.
- Wiedervorlage 30 Tage als globale Option; Ebenen darunter später möglich.
- Archiv und Papierkorb für Notes folgen dem Backlog.

### Open

- Ereignis-Auslöser: erlaubte Zielstatus, Verhalten bei bereits erfülltem Ziel
- Zustandsübergänge, Rücksetzen des Prüf-Datums
- Wer darf Änderungshinweise entscheiden; Rechte von Claude (Harness)
- Beförderung: Pflichtfelder; Rückstufung: Bedingungen
- Alter Label nach Projektwechsel (Widerspruch zu 'ändern sich nie' in STORY-038)
- STORY-047 wird Pflicht (Besitzer-Wunsch, Freigabe für Required for parent nötig)

## 2026-10-08 — Klärung: Projektwechsel, Fälligkeit, Notizen und Specs an Notes

### Discussed

- Label nach Projektwechsel
- Verhalten fälliger Notes und des Ausrufezeichens
- Übernahme von Notizen und Specs bei Beförderung und Rückstufung

### Decided

- Projektwechsel einer Note = im Zielprojekt neu anlegen (neues Label) und die alte löschen; die Link-Prüfungen greifen dabei automatisch. Labels ändern sich innerhalb eines Projekts nie, es gibt keine Alias-Labels.
- Ereignis-Auslöser: Zielstatus In progress, Awaiting confirmation, Completed, Rejected; ist das Ziel bei Anlage schon erreicht, feuert der Auslöser sofort und ist so markiert.
- Zustände und Prüf-Datum wie vorgeschlagen (Rücksetzen bei Anlage, Textänderung, Zurückstellen, behalten; gilt für alle Notes).
- Fällige Notes bleiben im Modal des roten Ausrufezeichens, bis sie zurückgestellt, erledigt, verworfen oder gelöscht sind. Das Icon bleibt, solange es Einträge gibt.
- Beförderung: Pflichtfelder liefert der Aufrufer, die UI zeigt ein vorausgefülltes Formular. Rückstufung: nur Status Open, ohne Kinder, nicht Parent oder Dependency eines anderen Items.
- Notes erhalten wie Items Notizen und Specs; sie wandern bei Beförderung und Rückstufung mit.
- Index mit Filtern Topic, Projekt, Status, fällig, verlinktes Item; dazu eine Zähler-Abfrage. UI: Ausrufezeichen neben dem Titel, Modal gruppiert nach Grund mit Schnellaktionen zum Zurückstellen, Zähler im Tab-Titel.
- Rechte von Claude (Harness): klärt der Besitzer im Harness.
- STORY-047 ist Pflicht (Required for parent: Yes); Goal, Kriterien und Titel angepasst.
- Markdown als Normalbetrieb abschaffen wird eigener Epic: EPIC-006.

### Open

- Untermotizen: Sollen Notes Unter-Notes haben (zusätzlich zu den Topics)? Das würde Modell (STORY-038), API (039), Beförderung (042) und UI (045) erweitern.
- Specs an Notes generieren: Soll das nur manuell oder auch aus der UI angestoßen werden?

## 2026-10-08 — Klärung: Untermotizen und Specs

### Discussed

- Was mit 'Subnotizen' gemeint ist

### Decided

- Es gibt keine Unter-Notes. Gemeint sind die Notizen- und Spec-Dokumente, die ein Backlog-Item hat; Notes bekommen dieselben Dokumente (bereits in STORY-038, 039 und 042 enthalten).
- Specs an Notes werden wie beim Backlog manuell oder per API angelegt, ohne eigene Generierung.

## 2026-10-08 — Umsetzungsblöcke (je eine Sitzung)

### Discussed

- Aufteilung in Blöcke, damit der Kontext je Sitzung klein bleibt und zusammengehörige Stories gebündelt sind

### Decided

- Block A: STORY-037 und 038 (Regeln, Datenmodell, Migration, Repository, Contract-Tests). Regeländerungen aus 037 brauchen vorher die Freigabe des Besitzers.
- Block B: STORY-040 und 043 (Auslöser, Wiedervorlage, Lebenszyklus, Archiv, Papierkorb als Domain und Services).
- Block C: STORY-039 (API und Index auf Block A und B).
- Block D: STORY-045 (UI). Danach ist der erste Schnitt nutzbar.
- Block E: STORY-041 und 042 (Änderungshinweise, Beförderung und Rückstufung).
- Block F: STORY-044 und 047 (projektübergreifende Links, Markdown-Sync).
- Block G: STORY-046 (Doku und Release).
- Geändert gegenüber der ersten Reihenfolge: 040 und 043 vor 039, weil der Index die Fälligkeit und das Archiv braucht.

### Open

- Dependencies zwischen den Blöcken sind im Backlog noch nicht gesetzt (braucht Freigabe).
