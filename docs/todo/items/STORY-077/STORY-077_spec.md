# `STORY-077` — Notes und Topics

Grundlage: `EPIC-007_spec.md`, Abschnitt 9 (`notes`). Verhalten wie im README des alten Viewers,
Abschnitt „Views → Notes“; dazu der Inhalt von `STORY-054` (Topic mit
Notizen löschen: Auswahldialog) und `STORY-055` (Topics archivieren und
reaktivieren).

## Datenmodell (fest)

- `notes_statuses(code PK)`: `waiting`, `due`, `snoozed`, `done`,
  `dropped`, `promoted`.
- `notes_topics(uid PK FK workspace_elements, name, parent_uid NULL,
  due_at NULL, archived_at NULL)`.
- `notes_notes(uid PK FK workspace_elements, summary, body, status FK,
  topic_uid NULL, review_at NULL, trigger_mode CHECK in ('any','all'),
  archived BOOL)`.
- `notes_documents(note_uid, name, content, revision, updated_at)`.
- `notes_settings(key PK, value)`: Prüf-Intervall, maximale Topic-Tiefe
  (Standard 3, Regel in der Domäne).

## Operationen

Wie `notes_api.py` heute: `index`, `show`, `create`, `update`, `keep`,
`snooze`, `finish`, `restore`, Topic-Operationen (`topic_create`,
`topic_update`, `topic_move`, `topic_archive`, `topic_reactivate`,
`topic_delete` mit Auswahl „archivierte Notizen behalten“ / „aktive
Notizen verschieben“), Dokumente wie `STORY-073`.

## Frontend

Hauptroute „Notes“ mit Baum (`STORY-067`), Filter Note-Status, Detail mit
Aktionen; Neu-Typen Note und Topic im Slot `workspace.create-types`;
Fällig-Zähler in `layout.header-actions` und im Tab-Titel; Einstellungen
Prüf-Intervall und Topic-Tiefe in `core.settings-sections`.

## Tests

Domäne zuerst (Status-Übergänge, Tiefe, Topic löschen/archivieren);
Repository gegen echte SQLite; UI-Tests Baum, Aktionen, Drag & Drop.
