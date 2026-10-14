# TASK-021 — Rotes Ausrufezeichen mit Zähler und Tab-Titel

## 2026-10-08 — Umsetzung

### Discussed

- Die Routen weichen von den Namen in der Spec ab und sind die des Backends (`/api/v2/notes/index`, `/api/v2/notes/due`, `/api/v2/notes/due/count`, `/api/v2/notes/settings`, `/api/v2/projects/{project}/notes/{label}/…`); Fehlercodes ebenso (`topic_too_deep` statt `topic_depth_exceeded`).

### Decided

- `useDueCount` fragt nur `GET /api/v2/notes/due/count`, alle 60 Sekunden und beim Fokussieren des Fensters; das Pausieren des Pollings (`pollingPause`) stoppt auch den Zähler (Standard wie beim Backlog).
- `tabTitle`/`badgeLabel` sind reine Funktionen (`99+` ab 100); das Icon erscheint nur bei Zähler > 0, ohne Blinken.
