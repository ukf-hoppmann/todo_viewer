# TASK-025 — Notes-Spiegel: Port und Datei-Adapter mit atomarem Schreiben

## 2026-10-14 — Spec an die Abstimmung vom 2026-10-14 angepasst

### Decided

- Alle Notes werden gespiegelt, auch archivierte und Papierkorb-Notes (vorher: nicht der Papierkorb).
- Zusätzlich counters.md und label-lose Notes (new-<kurzname>.md).
- Adapter-Paket infrastructure/notes_files/ bleibt (Import-Linter); die Pfadangabe infrastructure/markdown/ in der Story-Spec war falsch und ist korrigiert.

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.

### Decided

- Der Port ist dateiweise (`read`, `write(expected)`, `delete`, `fingerprint`, `files_with_markers`) statt Snapshot: Format und Regeln gehören nach `domain`, der Adapter bleibt ohne Notes-Logik; der Konflikt wird je Datei geprüft.
- Gelesen und angefasst werden nur Dateinamen des Formats; Spiegel-Ordner ist `<Markdown-Ordner>/notes/`; Schreiben über eine temporäre Datei im selben Ordner plus `os.replace`; Fehler `mirror_conflict` (409).

### Open

- Dateisysteme ohne atomares Umbenennen (Netzlaufwerke) nicht getestet.
