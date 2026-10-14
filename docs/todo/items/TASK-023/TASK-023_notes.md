# TASK-023 — Verlinkte Notes am Backlog-Item und Notes-Einstellungen

## 2026-10-08 — Umsetzung

### Discussed

- Die Routen weichen von den Namen in der Spec ab und sind die des Backends (`/api/v2/notes/index`, `/api/v2/notes/due`, `/api/v2/notes/due/count`, `/api/v2/notes/settings`, `/api/v2/projects/{project}/notes/{label}/…`); Fehlercodes ebenso (`topic_too_deep` statt `topic_depth_exceeded`).

### Decided

- `ItemNotes` im `DetailPanel` fragt mit dem Projektnamen des Items (`item.project`), nicht mit der Quell-ID; ohne Notes und Hinweise entfällt der Abschnitt.
- `NotesSettings` in „Allgemein“: `review_days` (1 bis 3650) und `max_topic_depth` (1 bis 10), Standardwerte als Platzhalter; Serverfehler erscheinen lokalisiert.
