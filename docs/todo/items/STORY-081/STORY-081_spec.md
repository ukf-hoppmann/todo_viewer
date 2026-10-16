# `STORY-081` — KI-Schnittstelle vollständig

Grundlage: `EPIC-007_spec.md`, Abschnitt 11.

## Umfang

- Gegenüberstellung als Tabelle in `docs/techdocs/interfaces.md`:
  Befehle von `backlog_api.py` (`health`, `sources`, `index`, `show`,
  `create`, `update`, `note`, `doc`, `put-doc`, `retype`, `delete`,
  `trash`, `restore`) und `notes_api.py` (alle Befehle aus `notes-api.md`
  des Harness) → MCP-Tool bzw. HTTP-Route. Fehlende Tools werden ergänzt.
- Ausgabeformen, die der Harness braucht: Index als kompakte Zeilen
  (`ID | Type | Status | Area | Title | Parent`), Item mit Version.
- Kein Tool für endgültiges Löschen und keine Einstellungsänderung (wie
  heute).
- Systemtest unter `tests/implementation/system/` mit eigenem Befehl in
  `tests/README.md`.

## Nicht im Umfang

Änderungen am Harness (macht der Projektinhaber nach dem Umstieg).
