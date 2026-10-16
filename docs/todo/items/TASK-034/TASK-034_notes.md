# TASK-034 — Architekturregeln für den Neubau schreiben und freigeben lassen

## 2026-10-16 — Entscheidungen aus der Architekturbesprechung

### Decided

- Wiederverwendbarkeit konsequent innerhalb des Projekts; kein eigenes Core-Paket.
- Zwei Speicher-Infrastrukturen (Datenbank, Dateien) und ein Sync-Dienst über beiden.
- SSE als Kanal Backend → Frontend; Wecker-Zeitgeber im laufenden Backend (Ausnahme von der heutigen Regel 3).
- Plugins aus fester Liste; Backend und Frontend getrennt.
