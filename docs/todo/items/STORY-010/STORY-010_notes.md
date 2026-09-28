# STORY-010 — Notizen

## 2026-09-28 — Zugangsvariante

### Discussed

- Varianten: Container läuft dauerhaft und wird per HTTP angesprochen;
  Server wird bei Bedarf gestartet; zusätzliches CLI ohne Server.

### Decided

- Variante „dauerhaft laufender Container, Zugriff per HTTP“.
- Wie ein Agent reagiert, wenn der Server nicht erreichbar ist, regelt das
  Claude_Harness; im ToDo-Viewer ist dafür nichts zu tun.
