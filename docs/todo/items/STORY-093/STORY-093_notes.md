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

## 2026-10-20 — Kompatibilität: Vorschläge angenommen, Migration und Abschaltung

### Discussed

- Frage des Owners: Wenn alle Einträge einmalig migriert werden, können die alten Endpunkte dann gleich nach dem Umbau entfallen?
- Die Migration betrifft die Daten; die alten Endpunkte braucht es wegen der Aufrufer (backlog_api.py des Harness, MCP-Tools, Cloud-Kopien des Plugins in den Projekten), die erst nachgezogen werden müssen.

### Decided

- Open vom 2026-10-20 (Version) erledigt: Version der zusammengesetzten Datei ist eine Zahl, die bei jeder Änderung von Kopf oder Protokoll steigt (Summe der Revisionen oder eigener Zähler; Wahl im Plan).
- Open vom 2026-10-20 (PUT ohne Stand) erledigt: Fehlt `## Stand`, bleibt der Kopf unverändert.
- Open vom 2026-10-20 (Stempelzeile) erledigt: Über die API ignoriert der Server die Stempelzeile im PUT-Text; im Spiegel wird sie übernommen.
- Open vom 2026-10-20 (Notes ohne Kopf) erledigt: Sie ergeben dieselbe Datei wie heute; geprüft per Rundlauf über alle bestehenden Notes.
- Alle bestehenden Notes werden einmalig migriert; danach gibt es nur noch Kopf- und Protokolltabellen.
- Die alten Endpunkte entfallen erst, wenn der Harness umgestellt ist und die Cloud-Kopien aktualisiert sind.

### Open

- Ob PUT auf die ganze Datei bleibt oder durch einen Endpunkt zum Bearbeiten einzelner Einträge ersetzt wird (mit dem Harness abstimmen).

## 2026-10-20 — Spec geschrieben, Abgleich mit dem Harness-Stand

### Discussed

- Der Harness hat inzwischen entschieden: Prüfsumme SHA-256 über das kanonische Protokoll, erste 12 Hex-Zeichen; Stempelzeile `Stand bestätigt nach Eintrag <Datum> — <Thema> (<Prüfsumme>)`; Hinweise ab 15 Beschlüssen und beim Umschreiben älterer Einträge; Umstellung Viewer zuerst, Notes ohne Kopf sind `missing`, kein Massenlauf für Köpfe.
- Scan der vorhandenen Notes (Viewer und Harness): Vorspann wie `## Summary`, eine Datei ohne Titelzeile, Notes ganz ohne datierte Einträge.

### Decided

- Open vom 2026-10-20 (verlustfreies Zerlegen) erledigt: Text zwischen Titelzeile und Kopf bzw. erstem Eintrag wird als Vorspann gespeichert; schlägt der Rundlauf in der Migration fehl, kommt der ganze Text in den Vorspann.
- Open vom 2026-10-20 (Version) erledigt: eigener Zähler `revision` für die Datei, `state_revision` für den Kopf; Anhängen ändert nur `revision`.
- `put_document` ändert den Stempel nie; der Spiegel übernimmt ihn aus der Datei und leert den Kopf, wenn `## Stand` in der Datei fehlt.
- Kopf bestätigen und einzeln bearbeiten gibt es in der Oberfläche in dieser Story nicht.
- Entfernen der alten Wege ist eine eigene Folge-Story nach dem Harness-Release.

### Open

- Testvektoren der Prüfsumme und der Fall eines leeren Protokolls mit dem Harness (TASK-021, TASK-022) abstimmen.
