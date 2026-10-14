# TASK-024 — Notes-Dateiformat: Serialisieren und Parsen mit Golden-Files

## 2026-10-14 — Format an die Abstimmung vom 2026-10-14 angepasst

### Decided

- Topic als Label statt Pfad; Created, Updated, Archived, Deleted gehören ins Format (vorher: Papierkorb wird nicht gespiegelt).
- Notes und Topics ohne Label (new-<kurzname>.md, NEW); counters.md für die Label-Zähler.
- Ein Eintrag je Zeile für Auslöser und Links, damit Git sauber zusammenführt.
