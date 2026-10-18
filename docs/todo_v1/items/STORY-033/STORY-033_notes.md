# STORY-033 — Einstellungsmenü: erweiterbarer Rahmen und Abschnitt „Allgemein“

## 2026-09-30 — Umsetzung und Entscheidungen

### Discussed

- Es gab keinen Endpunkt für Typ und Ort der Datenbank; dafür kam GET /storage dazu (nur lesend, ohne Passwort).
- Das Standard-Backend liegt im UI-Zustand (Feld defaultBackend über /ui-state), nicht im Browser-Speicher.

### Decided

- Das Menü besteht aus einer Abschnittsliste (components/settings/sections.tsx); ein neuer Abschnitt ist ein neuer Eintrag, initialSection öffnet bei einem Abschnitt (für STORY-034).
- Anfangswert des Standard-Backends bleibt markdown, damit sich ohne Zutun nichts ändert; im Menü auf Datenbank umstellbar.
- Release v0.6.6.

### Open

- Der Bearbeiten-Dialog und die Sync-Dialoge sind unverändert (STORY-034).
- Der Testserver im Browser-Pane lief aus dem Haupt-Checkout mit den echten Daten; ich habe ihn gestoppt und stattdessen einen Server mit Scratch-Konfiguration aus dem Worktree geprüft.
