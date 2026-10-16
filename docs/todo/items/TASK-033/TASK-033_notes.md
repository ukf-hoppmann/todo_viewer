# TASK-033 — Konflikte beim Sync entscheiden: Datenbank, Datei oder aufschieben

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.

### Decided

- `delete_missing` entfällt ganz (ein Aufruf damit ergibt 400 `bad_request`). `kept` meint aufgeschobene Löschungen, `deferred` alle aufgeschobenen Konflikte.
- Aufschieben hat keinen eigenen Zustand: Ein Konflikt ohne Entscheidung bleibt unberührt und wird beim nächsten Lauf wieder gemeldet.
- Schreibreihenfolge: erst die Datenbankseite (eine Transaktion, Backup davor), dann der Ordner. Entscheidungen für unbekannte oder nicht mehr bestehende Konflikte werden ignoriert.
- Das Token deckt beide Seiten und den gespeicherten Stand ab, die Entscheidungen gehören nicht dazu. Ein Projekt ohne Datenbank-Spiegel läuft immer nur `from_md`.

### Open

- Wird ein Item per Entscheidung gelöscht, auf das andere Items verweisen, bricht der Lauf mit `lifecycle_violation` (409) ab; die Datenbank bleibt dann unverändert.
- Gleichzeitigkeit mehrerer Prozesse nicht getestet (die Sperre gilt je Projekt im Prozess).
