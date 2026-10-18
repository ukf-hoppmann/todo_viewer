# `STORY-065` — Generischer Sync-Dienst

Grundlage: `EPIC-007_spec.md`, Abschnitt 7.3.

## Umfang

- Ports in `viewer.core.application.sync`:
  - `MirrorCodec`: `owner`, `patterns`, `decode(files: FileSet) -> list[MirrorEntry]`
    (wirft `MirrorFormatError(code, file, line)`),
    `encode(entries, current: FileSet) -> FileChanges` (verändert nur
    betroffene Einträge/Dateien),
  - `SyncParticipant`: `load(project) -> list[MirrorEntry]`,
    `apply(project, changes: SyncChanges, tx)`,
    `assign_labels(project, new_entries) -> Mapping[placeholder, label]`
    (vergibt über das Element-Register von `workspace`; bis `STORY-068` über einen Fake).
  - `MirrorEntry(uid: str | None, kind, label, placeholder: str | None, fields: Mapping, hash)`.
- Dienst `SyncService`: `status(project)`, `preview(project, direction) -> Preview(token, transfers, conflicts)`,
  `execute(project, token, decisions, delete_missing: bool)`, `auto(project)`.
- Vergleich je `uid` mit `core_sync_state`; Regeln aus §7.3. Reihenfolge
  der Teilnehmer nach `requires` (zuerst `workspace`-Daten, dann Plugins).
- Neue Einträge: `uid` erzeugen, Label über `assign_labels`, Verweise auf
  Platzhalter in allen Einträgen ersetzen, danach `encode` (Dateien
  umbenennen/neu schreiben).
- Auto-Sync: Takt `AUTO_SYNC_INTERVAL` (Standard 30 s) über den
  `Scheduler`, nur solange ein Projekt Auto-Sync an hat (Einstellung kommt
  aus `workspace`, hier über Port `MirrorSettings`).
- Ereignisse `core.sync.state` (public) nach jedem Lauf und bei
  Statusänderung.
- Operationen (HTTP + MCP) des Core: `sync_status`, `sync_preview`,
  `sync_execute`.
- Vor jedem Schreiben in die DB ein Backup (Grund `sync`).

## Nicht im Umfang

Konkrete Codecs (`STORY-075`, `STORY-079`, `STORY-080`), UI (`STORY-076`).

## Tests

Test zuerst: Domain-Funktion „Vergleich“ als reine Funktion (Tabellentests
aller Fälle aus §7.3); Integration mit Test-Plugin, echter SQLite und
temporärem Ordner; Auto-Sync mit fester Uhr.
