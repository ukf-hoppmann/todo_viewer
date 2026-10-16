# `STORY-064` — Infrastruktur Dateien

Grundlage: `EPIC-007_spec.md`, Abschnitt 7.2.

## Umfang

- Port `FileStore` in `viewer.core.application`:
  - `read(folder, patterns) -> FileSet` (Pfad → Text, Version = SHA-256),
  - `write(folder, changes, expected: Mapping[path, version | None])`,
    Änderungen sind Schreiben, Umbenennen, Löschen; alles oder nichts
    soweit das Dateisystem es zulässt (vorher alle Versionen prüfen),
  - `inspect(folder) -> FolderState` (fehlt, unlesbar, Merge-Marker mit
    Dateiliste, Git-Lock).
- Adapter `viewer.core.infrastructure.files`: atomares Schreiben (temporäre
  Datei im selben Ordner + `os.replace`), Zeilenenden der bestehenden Datei
  übernehmen, neue Dateien mit LF.
- Vorlagen aus dem Altcode (`backend/todo_viewer/infrastructure/markdown/text_file.py`,
  `merge_markers.py`, `notes_files/mirror.py`) dürfen als Vorlage gelesen und
  angepasst kopiert werden; kein Import aus dem Altcode.

## Nicht im Umfang

Formate (Codecs der Plugins), der Sync (`STORY-065`).

## Tests

Test zuerst: Contract-Suite `tests/implementation/integration/server/contract/test_file_store.py`
(atomar, Zeilenenden, Konflikt, Merge-Marker, Lock, fehlender Ordner).
