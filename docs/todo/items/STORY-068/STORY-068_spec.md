# `STORY-068` — Projekte, Suche und Element-Register

Grundlage: `EPIC-007_spec.md`, Abschnitt 9 (`workspace`).

## Datenmodell (fest)

- `workspace_projects(uid PK, name UNIQUE, mirror_folder NULL,
  mirror_enabled BOOL, auto_sync BOOL, sync_direction TEXT CHECK in
  ('both','to_files','to_database'), position INT, created_at)`.
  Eingebautes Projekt „Allgemein“ ohne Ordner (`STORY-060` Frage 2).
- `workspace_element_kinds(kind PK, owner, label_prefix)`; Präfixe:
  `EPIC`, `STORY`, `TASK`, `NOTE`, `TOPIC`, `ALARM`.
- `workspace_elements(uid PK, project_uid FK, kind FK, label, revision INT,
  created_at, updated_at, deleted_at NULL, UNIQUE(project_uid, label))`.
- `workspace_label_counters(project_uid, prefix, last INT)`.

## Ports für andere Plugins

`ElementRegistry`: `register(project, kind) -> Element` (vergibt `uid` und
Label), `relabel(uid, new_kind)` (Typwechsel: neues Label, `uid` bleibt),
`get`, `find_by_label(project, label)`, `bump_revision(uid, expected)`,
`mark_deleted`, `restore`, `purge`; `Projects`: lesen.

## Operationen (HTTP + MCP)

`list_projects`, `create_project`, `update_project`, `move_project`,
`remove_project` (nur leeres oder mit Bestätigung, Inhalte in den
Papierkorb), `browse_folders` (Startordner `BROWSE_START`), `resolve_label`.

## Frontend

- Plugin `workspace`: Seitenleisten-Abschnitte Suche und Projekte (Checkbox
  blendet ein/aus, Klick markiert, Reihenfolge per Drag & Drop, ✎ öffnet die
  Projektkarte, ↻ Auto-Sync, ⚠ Spiegel geändert — Werte kommen mit `STORY-076`).
- Neu-Dialog: Slot `workspace.create-types` (`{kind, title, icon, form}`);
  Knopf „＋ Neu“ in `layout.header-actions`. Ersetzt „＋ Neu“ und
  „＋ Note“ des alten Viewers.
- Öffentlicher Zustand: Suchtext, sichtbare und markierte Projekte
  (persistiert über UI-Zustand).

## Tests

Test zuerst: Label-Vergabe (nie wiederverwendet, auch nach Löschen und
Typwechsel), Register-Revision, Projekt-Operationen; UI-Tests der
Seitenleiste.
