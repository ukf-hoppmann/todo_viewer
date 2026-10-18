# STORY-087 — Browser-Logs ins viewer.log schreiben

## 2026-10-18 — Umsetzung

### Discussed

- Auslöser: Der Fehlerdialog im Abhängigkeiten-Graph ließ sich nur über die Browser-Konsole auswerten; ezf-ui schickt Logs ans Backend.

### Decided

- Operation client_log (POST /api/core/client-log, kein MCP-Tool) im Core; Logger viewer.client im viewer.log.
- Grenzen: Text 2000 Zeichen, error und data je 16 KiB, 100 Einträge je 60 s (darüber accepted=false).
- Client: BackendSink aus ezf-ui ohne Login, Wiederholung und Verbindungsmeldung; Fehler beim Senden nur als console.warn; in startApp mit Stufe warn.

### Open

- Sichtbar im laufenden Viewer erst nach Neubau des Images todo-viewer-next.
