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
