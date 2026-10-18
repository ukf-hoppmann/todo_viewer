# TASK-024 — Notes-Dateiformat: Serialisieren und Parsen mit Golden-Files

## 2026-10-14 — Format an die Abstimmung vom 2026-10-14 angepasst

### Decided

- Topic als Label statt Pfad; Created, Updated, Archived, Deleted gehören ins Format (vorher: Papierkorb wird nicht gespiegelt).
- Notes und Topics ohne Label (new-<kurzname>.md, NEW); counters.md für die Label-Zähler.
- Ein Eintrag je Zeile für Auslöser und Links, damit Git sauber zusammenführt.

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.

### Decided

- Zeitpunkte mit Bruchteilen von Sekunden stehen nur dort, wo sie vorhanden sind; die Kopfzeilen `Summary` bis `Deleted` stehen immer, `Triggers:` und `Links:` nur bei Einträgen; leerer Langtext und `None` sind dasselbe.
- Ein Event-Auslöser nennt das Ziel als `Projekt:Label` und den Status am Zeilenende. Notes und Topics ohne Label: `Topic: new:<Name>`, `note:new-<kurzname>`; Dateiname und Label müssen übereinstimmen.
- Bekannte Grenze (in der Doku genannt): Ein Link-Ziel `topic:` oder `note:` ist nicht von einem Projekt dieses Namens zu unterscheiden (Besitzer: bleibt).

### Open

- Der Harness (Dateimodus) wurde noch nicht gegen das Format geprüft.
