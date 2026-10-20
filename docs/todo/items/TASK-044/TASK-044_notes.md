# TASK-044 — Kopf-Endpunkte, Zustand und Hinweise für Item-Notes

## 2026-10-20 — Umsetzung abgeschlossen

### Discussed

- Umgesetzt im Worktree TASK-044: Prüfsumme, Zustand, Stempel und Hinweise in domain/notes.py; NotesStateService mit get, put, confirm, entries; append_note mit state/state_version; notes_state in get_item, list_items und index_lines; Systemtest über MCP mit dem Ablauf state, put-state, note, confirm-state, Einträge.
- Die Backlog-Ausgabe für Dokumente unterschied sich danach von der gleichnamigen des Notes-Plugins; im OpenAPI-Schema heißt sie jetzt ItemDocumentOut (Client: Alias DocumentOut bleibt).

### Decided

- Neue Notes mit Kopf beginnen mit Kopf-Version 1; jede Änderung von Kopf oder Stempel zählt sie hoch.
- notes_state steht auch in list_items (Feld mit Standard null), nicht nur in show und index.

### Open

- Lint des Clients meldet 5 Fehler in core/ui-state/usePersistentState.ts, die schon auf main bestehen.
- Container erst nach Rückfrage beim Owner aktualisieren.
