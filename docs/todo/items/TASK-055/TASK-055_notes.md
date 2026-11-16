# TASK-055 — Mindmap: Notizen an Knoten

## State

- Goal/Status: Offen, in Planung; Ort der Dokument-Logik entschieden (2026-11-16).
- Next step: Umsetzungsplan dem Owner vorlegen, nach Freigabe umsetzen.
- Open: keine
- Decided:
  - Die Dokumente eines Knotens liegen in einer eigenen Tabelle `mindmap_documents` im Plugin `mindmap`, mit schlankem Service nach dem Muster von `memos`; kein gemeinsamer Baustein im Workspace, kein `requires: backlog` (2026-11-16)
- References: Notizen `STORY-099`; Vorbild `server/src/viewer/plugins/memos/application/documents.py`; Baustein `client/src/shared/documents/DocumentsSection.tsx`

State confirmed after entry 2026-11-16 — Ort der Dokument-Logik (94109c54d15d)

## 2026-11-16 — Ort der Dokument-Logik

### Discussed

- Offener Punkt aus `STORY-099`: gemeinsamer Baustein im Workspace oder `requires: backlog`.
- Gemeinsamer Baustein im Workspace: generisch, spart künftige Kopien, aber ein großer Task, und backlog und memos müssten migriert werden.
- `requires: backlog`: die Dokumente dort hängen an Items (Label, Kurzfassung, Spiegel) und passen nicht zu Knoten.
- Eigene Tabelle im Plugin nach dem Muster von `memos`: kleine Migration, kein Eingriff in andere Plugins, knapp 100 Zeilen Duplikat.

### Decided

- Eigene Tabelle `mindmap_documents` im Plugin `mindmap` (Empfehlung angenommen)
- Open from 2026-11-16 (STORY-099: Ort der Dokument-Logik) resolved: eigene Tabelle im Plugin
