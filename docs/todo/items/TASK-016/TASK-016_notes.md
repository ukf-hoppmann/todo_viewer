# TASK-016 — Projektübergreifende Links und Ereignis-Auslöser prüfen und absichern

## 2026-10-08 — Umsetzung

### Discussed

- Sync-Weg geprüft: SyncService.run rief den Listener nicht; ein vom Sync eingespielter Statuswechsel löste keine Auslöser aus.

### Decided

- Neuer Fehlercode link_project_unknown (404) für Link-Ziele und Ereignis-Auslöser in nicht registrierten Projekten (vorher link_target_not_found bzw. source_gone); fehlendes Item in bekanntem Projekt bleibt link_target_not_found.
- LinkOut und TriggerOut haben target_display = 'Projekt · Label' (reine Funktion target_display in domain/notes.py).
- SyncService bekommt optional den ItemStatusListener (in bootstrap.py der NoteService). Ist das Sync-Ziel die Primärquelle, meldet run() jeden geänderten Item-Status per item_status_changed; Fehler des Listeners werden geloggt und lassen den Sync nicht scheitern. Sync in den Spiegel und Verschieben (from_md in eine noch nicht primäre Datenbank) melden nichts. Neue Items melden nichts.
- Tests: Zwei-Projekte-Fluss, already_met, Rückrichtung links-to, Markdown-Projekt als Ziel in tests/integration/test_notes_flow.py; Sync in tests/integration/test_sync.py.
