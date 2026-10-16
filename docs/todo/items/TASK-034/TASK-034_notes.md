# TASK-034 — Architekturregeln für den Neubau schreiben und freigeben lassen

## 2026-10-16 — Entscheidungen aus der Architekturbesprechung

### Decided

- Wiederverwendbarkeit konsequent innerhalb des Projekts; kein eigenes Core-Paket.
- Zwei Speicher-Infrastrukturen (Datenbank, Dateien) und ein Sync-Dienst über beiden.
- SSE als Kanal Backend → Frontend; Wecker-Zeitgeber im laufenden Backend (Ausnahme von der heutigen Regel 3).
- Plugins aus fester Liste; Backend und Frontend getrennt.

## 2026-10-16 — Regeln freigegeben

### Discussed

- Entwurf von architecture.md und den Scopes server, client und legacy vorgelegt.

### Decided

- Der Projektinhaber hat die Regeln unverändert freigegeben.
- Die bisherigen Regeln 1–3 gelten unverändert im Scope legacy für backend/** und web/**; die Scopes backend und web bleiben bis zum Umstieg.
- Mit den Scopes freigegebene Abhängigkeiten: server FastAPI, uvicorn, SQLAlchemy, Pydantic, mcp, structlog; client die Abhängigkeiten des ezf-ui-Core sowie @xyflow/react, elkjs, marked, dompurify und die Entwicklungswerkzeuge.
