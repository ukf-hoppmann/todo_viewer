# `STORY-079` — Notes im Markdown-Spiegel

Grundlage: `EPIC-007_spec.md`, Abschnitte 7.3, 10; Format: `docs/techdocs/interfaces.md`, Abschnitt „Dateiformat Version 2“; Beispiele unter `tests/fixtures/mirror-v2/`.

## Umfang

- `MirrorCodec` für `notes/**` (Notes, Dokumente, `topics.md`); Vorlage
  `src_old/backend/todo_viewer/domain/notes_markdown.py` und
  `application/services/notes_sync.py`, angepasst an `Uid` und ohne
  `counters.md`.
- Verknüpfungen der Note stehen in ihrem Kopf (`Links`) als
  `<projekt>:<LABEL>` mit Rolle; beim Import über `resolve_label` zu `uid`.
- `SyncParticipant` mit `ElementRegistry` und `Links`.

## Tests

Golden-Files; Platzhalter; Verweise über Projekte; Integration mit dem
Sync-Dienst.
