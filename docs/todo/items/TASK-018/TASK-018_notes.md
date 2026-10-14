# TASK-018 — Notes-Bereich: Gerüst, Topic-Baum und Notes-Liste

## 2026-10-08 — Umsetzung

### Discussed

- Die Routen weichen von den Namen in der Spec ab und sind die des Backends (`/api/v2/notes/index`, `/api/v2/notes/due`, `/api/v2/notes/due/count`, `/api/v2/notes/settings`, `/api/v2/projects/{project}/notes/{label}/…`); Fehlercodes ebenso (`topic_too_deep` statt `topic_depth_exceeded`).

### Decided

- Der Bereich ist ein weiterer Reiter neben Baum, Graph, Kanban und Papierkorb (kleinster Eingriff in `App.tsx`); der Detail-Panel des Backlogs ist dort ausgeblendet.
- UI-Zustand (`state/uiState.ts`): `notesProject`, `notesTopic` und `selectedNote` (je Projekt plus Label, weil Labels je Projekt zählen) und die Aktionen `notesScope`, `selectNote`, `openNote` (springt in den Bereich).
- Die Liste wird im Browser aus dem Index geschnitten (`domain/notes.ts`: `buildTopicTree`, `notesOfTopic` mit Unter-Topics, `topicPath`, `sortNotes`); das Topic wird mit seinem Projekt gewählt.
- Topic-Aktionen am gewählten Topic: Unter-Topic, Umbenennen, Termin, Verschieben, Löschen; ein Topic mit Inhalt fragt vor dem Mitlöschen nach (`topic_has_content`).
- Tests je Bereich in eigenen Dateien (`notes.test.tsx`, `noteDetail.test.tsx`, `triggers.test.tsx`, `dueBadge.test.tsx`, `conversion.test.tsx`, `dueModal.test.tsx`, `itemNotes.test.tsx`) statt in einer; gemeinsame Stub-Hilfen in `src/test/api.ts`.
