# TASK-020 — Notes-Bereich: Auslöser anzeigen, bearbeiten und Zurückstellen

## 2026-10-08 — Umsetzung

### Discussed

- Die Routen weichen von den Namen in der Spec ab und sind die des Backends (`/api/v2/notes/index`, `/api/v2/notes/due`, `/api/v2/notes/due/count`, `/api/v2/notes/settings`, `/api/v2/projects/{project}/notes/{label}/…`); Fehlercodes ebenso (`topic_too_deep` statt `topic_depth_exceeded`).

### Decided

- Reine Funktionen in `domain/notes.ts`: `snoozePresets(now)` (morgen, in einer Woche, in 30 Tagen, je 08:00 Ortszeit; Monats-, Jahres- und Sommerzeitwechsel sind getestet), `toIsoWithZone`, `toLocalInput`, `alreadyMet`, `describeTrigger`.
- Der Modus any/all wird nicht angezeigt; neue Notes bekommen `any`, vorhandene behalten ihren Wert.
- Ein Ereignis mit schon erreichtem Zielstatus wird vor dem Speichern gemeldet (Status aus dem Backlog); der Server bleibt maßgeblich (`already_met`).
- Item-Auswahl über `useBacklog`-Daten (`items` aus `App`) mit `ItemPicker`; die Index-Route war nicht nötig. Der Termin eines Topics steht im Topic-Menü („Termin“).
