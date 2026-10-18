# `STORY-073` — Backlog-Dokumente

Grundlage: `EPIC-007_spec.md`, Abschnitt 9.

## Datenmodell

`backlog_documents(item_uid FK, name, content TEXT, revision INT,
updated_at, PRIMARY KEY(item_uid, name))`. Der Name folgt dem Label; beim
Typwechsel werden Namen umbenannt (Vorlage `domain/documents.py`).

## Operationen

`list_documents(item)`, `get_document(item, name)` mit Version,
`put_document(item, name, version|new, content, summary?)`,
`append_note(item, topic, discussed, decided, open, summary?)`.

## Frontend

Abschnitt „Dokumente“ im Detailpanel; Dokument-Dialog mit `MarkdownView`,
`MarkdownEditor`, „＋ Notiz-Eintrag“, „＋ Spec anlegen“.

## Tests

Test zuerst: Format des Notiz-Eintrags, Umbenennen beim Typwechsel,
Versionskonflikt.
