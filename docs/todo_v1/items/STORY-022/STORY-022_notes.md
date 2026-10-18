# STORY-022 — Projekte und UI-State in der zentralen Datenbank

## 2026-09-30 — Plan freigegeben

### Discussed

- Entfernen eines Datenbank-Projekts, das Items hat.
- Zeitpunkt der Übernahme aus config.json und ui_state.json.

### Decided

- DELETE /sources lehnt Datenbank-Projekte mit Items ab (project_not_empty, 409); leere lassen sich entfernen.
- Übernahme beim ersten Zugriff auf Projekte bzw. UI-State; Sicherungen config.json.bak und ui_state.json.bak; DB-Quellen aus STORY-021 ziehen samt Items unter neuer UUID um.
- PUT /sources lehnt einen Backend-Wechsel ab (backend_change_not_supported); der Wechsel läuft über den Sync (STORY-023).
- Die Datenbankdatei entsteht jetzt immer, weil die Projektliste in ihr liegt.
