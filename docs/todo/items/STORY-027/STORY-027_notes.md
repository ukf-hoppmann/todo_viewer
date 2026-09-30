# STORY-027 — Dokument-Port itembasiert statt pfadbasiert

## 2026-09-30 — Plan freigegeben

### Discussed

- Alle 105 Notes-/Spec-Verweise der konfigurierten Backlogs haben die Form items/<ID>/<Datei>.

### Decided

- Item.notes/spec enthalten Dokumentnamen; der Markdown-Adapter übersetzt Pfade und schreibt sie bei ID-Wechsel neu.
- Fremde Pfade bleiben als Name mit '/' erhalten und werden beim Typwechsel nicht umbenannt.
- Die Version von Items mit Dokumenten ändert sich einmalig; in JSON-Goldens ändern sich nur version-Werte.
- Kein Release, weil nur intern.
