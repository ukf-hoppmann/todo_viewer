# TASK-026 — Notes in den gemeinsamen Sync aufnehmen

## 2026-10-14 — Umbau auf den gemeinsamen Sync

### Decided

- Kein eigener Notes-Sync mehr (keine notes-sync-Routen, keine Tabelle notes_sync_state, keine eigenen Richtungen und Kollisionsentscheidungen): Notes laufen im bestehenden Sync mit dem Stand je Eintrag und den Entscheidungen Datenbank, Datei oder aufschieben aus STORY-057.
- Label-Kollisionen entfallen als Sonderfall, weil nur die Datenbank Labels vergibt (Notes ohne Label aus der Cloud).
- Neue Abhängigkeit auf TASK-033.

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.
- Prüfung an einer Kopie der echten Datenbank (Temp-Pfade, echte Ordner nicht berührt): Round-Trip Datenbank → Dateien → leere Datenbank für `ToDo_viewer` und `ezf-ui`. Notes (10, davon 5 archiviert oder gelöscht), Topics (4, eines gelöscht), Dokument, Links (11), Auslöser (4) und Zähler waren danach tabellenweise identisch; eine zweite Vorschau nach dem Lauf war leer.

### Decided

- Neue Eintragsarten `topic`, `note`, `note_document` im selben Stand je Eintrag; Notes ohne Label (`new-…`, `NEW`) sind immer „im Ordner neu“, die Datenbank vergibt das Label und die Datei wird im selben Lauf umbenannt (samt Dokumenten, Verweisen, `topics.md`). Bei `from_md` werden sie nicht übernommen.
- Löschen per Entscheidung heißt endgültig entfernen (`purge`) mit Dokumenten und Links. Format-Fehler brechen den Sync vor jeder Änderung ab (`sync_source_invalid`, `reason=note_format`).
- `counters.md` wird nur zusammen mit anderen Notes-Änderungen geschrieben (Besitzer); Todo-IDs bekommen keine automatische Nummernvergabe, Kollisionen sind Konflikte (Besitzer).
- Der Gesamt-Fingerabdruck umfasst Notes nur, wenn es welche gibt; Projekte mit Notes gelten nach dem Update einmalig als geändert.

### Open

- Auslöser mit `fired_at` oder `already_met` kommen in den echten Daten nicht vor; sie sind nur durch Tests abgedeckt.
- Laufzeit bei sehr vielen Notes nicht gemessen; echter Cloud-Lauf (claude.ai) mit Git nicht geprüft.
