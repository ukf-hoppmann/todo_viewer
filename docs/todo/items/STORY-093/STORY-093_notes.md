# STORY-093 — Item-Notes mit Kopf und Protokoll: getrennt gespeichert, Stempel und Zustand

## 2026-10-20 — Anforderung aus dem Harness (STORY-051) und Einordnung

### Discussed

- Der Harness (Claude_Harness, STORY-051, Spec-Abschnitt „Schnittstelle zum ToDo-Viewer“) will Item-Notes mit Kopf („## Stand“) und Protokoll; ein Stempel mit der Prüfsumme des Protokolls zeigt, ob der Kopf nach Änderungen geprüft wurde.
- Gemeint sind die Item-Notes (<ID>_notes.md), nicht das Notes-Plugin (Merkzettel, Topics, Wecker).
- Heute liegt jede Notes-Datei als ein Text in backlog_documents; append_note hängt nur Text an; Kopf und Protokoll teilen sich eine Revision.
- Beim Typwechsel wird nur der Dateiname umbenannt, die Titelzeile `# <Label> — <Titel>` in der Datei bleibt beim alten Label.

### Decided

- Kopf und Protokolleinträge kommen in eigene Tabellen: getrennte Revisionen vermeiden Versionskonflikte zwischen Anhängen und Kopf-Bearbeitung, und der Kopf lässt sich ohne Protokoll laden.
- Specs bleiben in backlog_documents.
- Die Story hängt unter EPIC-007, nicht erforderlich für das Epic.

### Open

- Zerlegen und Zusammensetzen muss verlustfrei sein: Platz für Text vor dem ersten Datumsabschnitt und für Überschriften, die nicht dem Muster folgen (z. B. ein Vorspann-Eintrag).
- Gemeinsame Testbeispiele für die Prüfsumme mit dem Harness abstimmen (Definition in format.md des Harness).
- Im Harness noch offen und für das Verhalten der Endpunkte relevant: Längenhinweis für den Kopf, Warnung beim Umschreiben älterer Einträge, Umgang mit bestehenden Notes-Dateien. Plan erst nach deren Klärung.
- Die nicht committeten UI-Änderungen an ItemDetail, DocumentsSection und MarkdownView vorher abschließen.

## 2026-10-20 — Rückwärtskompatibilität der bisherigen Endpunkte

### Discussed

- Bisherige Endpunkte: GET /items/{ref}/documents, GET/PUT /items/{ref}/documents/{name}, POST /items/{ref}/notes, dazu die gleichnamigen MCP-Tools.
- Knackpunkte: eine gemeinsame Version für die zusammengesetzte Datei, PUT von Clients, die den Kopf nicht kennen, die Stempelzeile im PUT-Text, Notes ohne Kopf.

### Decided

- Die bisherigen Endpunkte bleiben gültig: GET setzt Kopf und Protokoll zur Datei zusammen, PUT zerlegt sie wieder, POST …/notes hängt wie bisher an; neue Felder (z. B. `state`) sind nur Zusätze.
- Die neuen Endpunkte kommen daneben; die alten werden entfernt, wenn der Harness nachgezogen ist.

### Open

- Gemeinsame Version der zusammengesetzten Datei (Vorschlag: Summe der Revisionen von Kopf und Protokoll oder ein eigener Zähler).
- PUT ohne Abschnitt `## Stand`: Kopf unverändert lassen (Vorschlag) oder leeren.
- Stempelzeile im PUT-Text über die API ignorieren (Vorschlag: der Server setzt den Stempel), im Spiegel übernehmen.
- Notes ohne Kopf ergeben dieselbe Datei wie heute (Vorschlag; Prüfung mit allen bestehenden Notes).
- Prüfen, ob der Harness im Files-Modus (Cloud-Kopie) mit `## Stand` und Stempelzeile im Spiegel zurechtkommt.
- Ob GET/PUT auf die ganze Datei überhaupt entfallen sollen; die Spec im Harness sieht sie dauerhaft vor.
