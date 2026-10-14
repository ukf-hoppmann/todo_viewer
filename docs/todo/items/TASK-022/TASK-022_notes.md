# TASK-022 — Fällig-Modal mit Gruppierung und Aktionen

## 2026-10-08 — Umsetzung

### Discussed

- Die Routen weichen von den Namen in der Spec ab und sind die des Backends (`/api/v2/notes/index`, `/api/v2/notes/due`, `/api/v2/notes/due/count`, `/api/v2/notes/settings`, `/api/v2/projects/{project}/notes/{label}/…`); Fehlercodes ebenso (`topic_too_deep` statt `topic_depth_exceeded`).
- Die Fällig-Liste kennt keine Version der Note.

### Decided

- Gruppen in fester Reihenfolge: Auslöser, Änderungshinweis, Termin, Prüfung (`groupDueByReason`); `rowActions` ergänzt „Befördern“ für Nicht-Hinweise und „Öffnen“ für alle; `nextAfterAction` bestimmt den Fokus.
- Erledigen, Verwerfen und Behalten lesen die Note unmittelbar vor der Aktion und handeln auf deren aktueller Version; Zurückstellen und Befördern laden die Note beim Öffnen des Dialogs.
- Bei Hinweis-Zeilen steht je offenem Hinweis die Ursache (`describeNotice`) mit behalten, abkoppeln, verwerfen und befördern; „Befördern“ entscheidet den Hinweis mit.
- Die Liste wird nur bei offenem Modal geladen und nach jeder Aktion neu gelesen; ein Fehler lässt die Zeile samt Meldung stehen; ist die Liste nach einer Aktion leer, schließt das Modal.
