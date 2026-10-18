# TASK-019 — Notes-Bereich: Detailansicht, Dokumente und Links

## 2026-10-08 — Umsetzung

### Discussed

- Die Routen weichen von den Namen in der Spec ab und sind die des Backends (`/api/v2/notes/index`, `/api/v2/notes/due`, `/api/v2/notes/due/count`, `/api/v2/notes/settings`, `/api/v2/projects/{project}/notes/{label}/…`); Fehlercodes ebenso (`topic_too_deep` statt `topic_depth_exceeded`).

### Decided

- `DocumentDialog` wird über ein `DocumentBackend` (Lesen, Schreiben, Anhängen, Nachladen) für Items und Notes genutzt; die Item-Fassung ist unverändert (`itemBackend`), Notes nutzen `noteBackend` in `NoteDocuments.tsx`.
- `NoteDetail` wird erst beim Öffnen einer Note geladen (web.md §4: der Markdown-Renderer bleibt im eigenen Chunk).
- Bearbeiten speichert mit der Version beim Öffnen des Formulars; bei `version_conflict` zeigt es die Meldung und „Neu laden“ holt den Stand und füllt das Formular neu.
- Links: `trigger` und `origin` werden angezeigt, aber nicht gelöst; gesetzt werden nur Verweise (Item eines beliebigen Projekts über `ItemPicker`, Topic, andere Note). `reachable=false` erscheint als „nicht erreichbar“.
- Geschlossene und gelöschte Notes sind schreibgeschützt (Hinweis statt Aktionen).
