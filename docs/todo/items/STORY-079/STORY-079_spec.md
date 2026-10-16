# `STORY-079` — Notes im Markdown-Spiegel

Grundlage: `EPIC-007_spec.md`, Abschnitte 7.3, 10; Format aus `TASK-035`.

## Umfang

- `MirrorCodec` für `notes/**` (Notes, Dokumente, `topics.md`); Vorlage
  `backend/todo_viewer/domain/notes_markdown.py` und
  `application/services/notes_sync.py`, angepasst an `Uid` und ohne
  `counters.md`.
- Verknüpfungen der Note stehen in ihrem Kopf (`Links`) als
  `<projekt>:<LABEL>` mit Rolle; beim Import über `resolve_label` zu `uid`.
- `SyncParticipant` mit `ElementRegistry` und `Links`.

## Tests

Golden-Files; Platzhalter; Verweise über Projekte; Integration mit dem
Sync-Dienst.
