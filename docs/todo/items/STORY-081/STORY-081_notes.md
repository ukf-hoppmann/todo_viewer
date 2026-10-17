# STORY-081 — Notizen

## 2026-10-17 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Gegenüberstellung.** Die Befehle von `backlog_api.py` (`.claude-harness/runtime/scripts/`) und `notes_api.py` (Beschreibung `.claude/skills/harness-todo/notes-api.md`) werden Befehl für Befehl den Tools zugeordnet (`interfaces.md`, neuer Abschnitt „MCP-Tools für den Harness“). Was fehlt, wird ergänzt.
- **Lücken** nach Abgleich mit den vorhandenen Operationen: (1) `health` hat kein Tool → `core_health`; (2) Index als kompakte Zeilen → `backlog_index_lines`, `notes_index_lines`; (3) Projektwechsel einer Note (`move`) fehlt ganz → `notes_move_note`; (4) die Einstellungen der Notes sind lesbar, aber nicht als Tool → `notes_get_notes_settings` wird MCP-Tool (Ändern bleibt HTTP-only, wie heute); (5) Zeit-Auslöser (`trigger-add` mit `time`) gibt es nicht mehr, der Wecker ersetzt sie (Entscheidung aus STORY-078), steht in der Tabelle. `backlinks`, `notes-of-item`, `links` laufen über `workspace_list_links`, `sources` über `workspace_list_projects`, Papierkorb und Löschen über `workspace_*`.
- **Namen.** Die Operation `notes_index` hieße als Tool `notes_notes_index`; sie heißt künftig `index` (Tool `notes_index`). Der Client ruft Pfade, nicht Operationsnamen: keine Folgen außer dem neu erzeugten `schema.d.ts`.
- **Systemtest** `tests/implementation/system/server/test_harness_flow.py`: echter uvicorn-Server mit allen Plugins, MCP-Client; Ablauf Index, Anlegen, Ändern mit Version (und `version_conflict`), Notiz anhängen, Note anlegen und verknüpfen, Wecker stellen und erledigen, Löschen, Papierkorb, Wiederherstellen. Eigener Befehl in `tests/README.md`; `check-next.sh` und `pytest` nehmen ihn mit auf.
- Der Plan entstand erst nach dem Abgleich der Operationen (der Abgleich war nötig, um die Lücken zu kennen); es wurde nichts vor dem Plan gebaut.

### Decided

1. Server: `core_health`, Index-Zeilen, `notes_move_note` (mit Tests), Settings-Tool.
2. Systemtest.
3. Techdoku (`interfaces.md`, `neubau-server.md`, `tests/README.md`), `check-next.sh`, `check.sh`, Status.

### Open

- Keine neuen Fragen.

## 2026-10-17 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Wie geplant. `notes_move_note` (`RelocationService`) übernimmt Texte, Status, Prüfdatum, Dokumente (Namen auf das neue Label), Verweise und Ereignis-Auslöser; der Topic-Termin-Auslöser entfällt, weil das Topic wechselt. Die alte Note kommt in den Papierkorb, die Antwort ist die neue Note.
- `workspace_delete_element` und `backlog_get_item` verlangen `uid`; der Harness löst ein Label einmal über `get`/`resolve_label` auf (in der Tabelle vermerkt).

### Decided

- Abschlusskriterien geprüft: (1) Gegenüberstellung vollständig, jeder Befehl beider Helfer hat ein Tool oder eine Route (`interfaces.md`); (2) Systemtest `test_harness_flow.py` grün; (3) `interfaces.md` beschreibt die MCP-Tools; (4) Tests grün (`test_note_relocation.py`, `test_note_index_lines.py`, `test_mcp.py`, Systemtest), `check-next.sh` und `check.sh` grün. Status: `Awaiting confirmation`.

### Open

- Nicht geprüft: ein echter MCP-Client des Harness (nur der MCP-Client der Bibliothek im Test); die Anpassung des Harness selbst ist nicht Teil dieser Story.
- `workspace_delete_element` nimmt nur `uid`; ein Label-Aufruf wie `delete NOTE-004` braucht beim Harness einen Schritt mehr.
