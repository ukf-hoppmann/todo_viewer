# TASK-015 — UI-Dialoge für Beförderung und Rückstufung

## 2026-10-08 — Umsetzung

### Discussed

- Die Routen weichen von den Namen in der Spec ab und sind die des Backends (`/api/v2/notes/index`, `/api/v2/notes/due`, `/api/v2/notes/due/count`, `/api/v2/notes/settings`, `/api/v2/projects/{project}/notes/{label}/…`); Fehlercodes ebenso (`topic_too_deep` statt `topic_depth_exceeded`).
- TASK-015 wurde zusammen mit STORY-045 umgesetzt, weil TASK-022 den `PromoteNoteDialog` braucht (Entscheidung des Besitzers).

### Decided

- `PromoteNoteDialog` startet mit Titel, Zusammenfassung und Ziel aus der Note (`domain/conversion.ts`); mit `notice` läuft er über die Entscheidung `promote` des Hinweises (Fällig-Modal), sonst über `…/promote`.
- `DemoteItemDialog` ist nur im Status Open erreichbar; Ablehnungen (`demote_*`) erscheinen als lokalisierte Texte.
- Herkunft: `ItemOrigin` („Aus Note …“) im `DetailPanel`, `NoteOrigin` („Herkunft: Item …“ bzw. „Wurde zu Item …“) in der Note.
