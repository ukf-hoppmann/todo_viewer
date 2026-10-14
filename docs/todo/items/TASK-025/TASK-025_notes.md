# TASK-025 — Notes-Spiegel: Port und Datei-Adapter mit atomarem Schreiben

## 2026-10-14 — Spec an die Abstimmung vom 2026-10-14 angepasst

### Decided

- Alle Notes werden gespiegelt, auch archivierte und Papierkorb-Notes (vorher: nicht der Papierkorb).
- Zusätzlich counters.md und label-lose Notes (new-<kurzname>.md).
- Adapter-Paket infrastructure/notes_files/ bleibt (Import-Linter); die Pfadangabe infrastructure/markdown/ in der Story-Spec war falsch und ist korrigiert.
