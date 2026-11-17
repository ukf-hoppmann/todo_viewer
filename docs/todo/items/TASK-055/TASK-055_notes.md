# TASK-055 — Mindmap: Notizen an Knoten

## State

- Goal/Status: Abgeschlossen: vom Owner bestätigt (2026-11-16), nach `todo_mindmap` gemergt.
- Next step: keiner; `STORY-099` prüft, ob ihre Kriterien erfüllt sind.
- Open:
  - `test_client_log.py::test_browser_entry_lands_in_the_server_log` schlägt auch ohne diese Änderung fehl; der Lint meldet weiter die Fehler in `usePersistentState.ts` und `backlog/domain/editing.py` (2026-11-16)
- Decided:
  - Die Dokumente eines Knotens liegen in einer eigenen Tabelle `mindmap_documents` im Plugin `mindmap`, mit schlankem Service nach dem Muster von `memos`; kein gemeinsamer Baustein im Workspace, kein `requires: backlog` (2026-11-16)
  - Die Art eines Dokuments folgt aus Name und Label (keine Spalte `kind`); die Kopfzeile der Notiz nennt den Titel des Knotens (2026-11-16)
  - `NodeOut` und der Baum tragen `documents` (die Namen); daran erkennt die Map Knoten mit Notizen, ein Symbol im Knoten (2026-11-16)
  - Knoten im Papierkorb lassen sich lesen, aber nicht beschreiben (`mindmap_node_deleted`); einen Papierkorb für einzelne Dokumente gibt es nicht (2026-11-16)
- References: Notizen `STORY-099`; Vorbild `server/src/viewer/plugins/memos/application/documents.py`; Baustein `client/src/shared/documents/DocumentsSection.tsx`; Schnittstelle in `docs/techdocs/neubau-server.md` (Plugin `mindmap`, Dokumente)

State confirmed after entry 2026-11-16 — Bestätigung und Merge (43f182f75c82)

## 2026-11-16 — Ort der Dokument-Logik

### Discussed

- Offener Punkt aus `STORY-099`: gemeinsamer Baustein im Workspace oder `requires: backlog`.
- Gemeinsamer Baustein im Workspace: generisch, spart künftige Kopien, aber ein großer Task, und backlog und memos müssten migriert werden.
- `requires: backlog`: die Dokumente dort hängen an Items (Label, Kurzfassung, Spiegel) und passen nicht zu Knoten.
- Eigene Tabelle im Plugin nach dem Muster von `memos`: kleine Migration, kein Eingriff in andere Plugins, knapp 100 Zeilen Duplikat.

### Decided

- Eigene Tabelle `mindmap_documents` im Plugin `mindmap` (Empfehlung angenommen)
- Open from 2026-11-16 (STORY-099: Ort der Dokument-Logik) resolved: eigene Tabelle im Plugin

## 2026-11-16 — Umgesetzt

### Discussed

- Server: Domain `domain/documents.py` (Namen, Notiz-Eintrag), Tabelle `mindmap_documents` (Migration v2), `DocumentService` und vier Operationen (`list_node_documents`, `get_node_document`, `put_node_document`, `append_node_entry`) samt Ereignis `mindmap.document.changed`.
- Client: `DocumentsSection` des Plugins (Mantel um den gemeinsamen Baustein), Abschnitt „Dokumente“ im Detail, Notiz-Symbol am Knoten, API-Typen neu erzeugt.
- Geprüft: Server 1153 und Client 1245 Tests grün (außer dem bekannten `test_client_log`), mypy und Importregeln sauber, Ablauf im Browser (Notiz anlegen, Symbol erscheint, Dokument öffnen).

### Decided

- `TASK-055` steht auf `Awaiting confirmation`
- Open from 2026-11-16 (Ort der Dokument-Logik) bleibt geschlossen: eigene Tabelle im Plugin

### Open

- Der Test `test_client_log.py::test_browser_entry_lands_in_the_server_log` und die Lint-Fehler in `usePersistentState.ts` und `backlog/domain/editing.py` bestanden vorher

## 2026-11-16 — Bestätigung und Merge

### Decided

- Der Owner hat `TASK-055` bestätigt; es ist `Completed` und nach `todo_mindmap` gemergt
