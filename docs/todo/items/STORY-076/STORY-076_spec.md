# `STORY-076` — Sync in der Oberfläche

Grundlage: `EPIC-007_spec.md`, Abschnitte 7.3, 8. Verhalten wie im README des alten Viewers,
Abschnitte „Quellen konfigurieren“ und „Einstellungen“, ohne Wechsel der
Primärquelle.

## Umfang

- Plugin `workspace` (Frontend): Abschnitt „Projekte“ in
  `core.settings-sections` mit Projektkarten; Sync-Dialog; Werte ⚠/↻ in der
  Projektliste.
- Nutzt die Core-Operationen `sync_status`, `sync_preview`, `sync_execute`
  (`STORY-065`) und `update_project` (`STORY-068`) für Spiegel-Einstellungen.
- SSE-Topic `core.sync.state` → Status neu laden.
- Vorlage: `web/src/components` (Sync-Dialog, Projektkarte).

## Tests

UI-Tests mit gemockter API für Vorschau, Konflikt-Entscheidung, Sammelknöpfe,
Statusanzeige.
