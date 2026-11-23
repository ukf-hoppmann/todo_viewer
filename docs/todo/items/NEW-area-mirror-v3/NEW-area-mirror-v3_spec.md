# NEW-area-mirror-v3 — Spec: Backlog-Spiegel Format Version 3

Zu `STORY-106` (Area entfällt). Die Entscheidung steht in `STORY-106_notes.md`: Area entfällt ganz, das Format wird
Version 3, ein Import mit dem Feld darf nie abstürzen.

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.

## Umfang

- Nur der Backlog-Teil des Spiegels (`TODO.md`, `archive.md`, `items/**`). Alarme (`alarms.md`, trägt weiter „backlog
  format version 2“) und Memos (`memos/`) bleiben unverändert.
- Stellen im Code (Zeilen können sich verschoben haben, mit `grep -n -i area` prüfen):
  `server/src/viewer/plugins/backlog/infrastructure/mirror/`
  - `encode.py`: Kennung „backlog format version 2“ in den Vorlagen für `TODO.md` und `archive.md` (zwei Stellen),
    `values["Area"] = f["area"]`.
  - `syntax.py`: `FORMAT_VERSION` (Regex der Kennung) und die Feldliste mit `"Area"`.
  - `decode.py`: `need("Area")` und `"area": area` in den Feldern; die Prüfung der Kennung (`format_version`) muss 2
    und 3 zulassen.
  - `participant.py`: `"area": item.area` beim Laden, `area=f["area"]` beim Anlegen und Ändern (zwei Stellen) →
    Area weder laden noch aus den Feldern lesen; ein Item aus den Dateien bekommt `area=None`.
- Das Modell `Item.area` und die Datenbank bleiben in dieser Task unverändert (sie folgen in der Task zum Entfernen
  auf dem Server). Folge, gewollt: Werte von Area in der Datenbank können beim Übernehmen aus Dateien leer werden.

## Regeln des Formats

- Version 3 = Version 2 ohne das Feld `Area`. Felder und Reihenfolge: `Uid`, `Type`, `Parent`,
  `Required for parent`, `Status`, `Created`, `Priority`, `Dependencies`, `Goal`, `Completion criteria`, `Summary`,
  `Resolution`, `Deleted`.
- Pflichtfelder: wie Version 2, aber ohne `Area`.
- Lesen: `Area` ist in jeder Version ein bekanntes, ignoriertes Feld (kein `unknown_field`, kein `missing_field`).
  Beim nächsten Schreiben entfällt die Zeile (der Codec ändert nur die betroffenen Einträge; ein unveränderter
  Eintrag wird nicht allein wegen Area umgeschrieben, ein umgeschriebener verliert sie).
- Schreiben: immer Version 3, auch wenn die Datei vorher Version 2 trug (die Kennung im Kopf der Datei wird
  ersetzt).

## Tests

- Unit: `tests/implementation/unit/server/plugins/backlog/test_mirror_encode.py` und `test_mirror_decode.py`
  anpassen und ergänzen (Version 3 schreiben; Version 2 mit Area lesen; Version 3 mit Area lesen; Version 4
  abweisen).
- Integration: `tests/implementation/integration/server/plugins/backlog/test_item_mirror.py` (Sync mit Dateien ohne
  Area).
- Fixtures: `tests/fixtures/mirror-v3/` nach dem Muster von `tests/fixtures/mirror-v2/` (README, `valid`, `invalid`)
  für den Backlog-Teil; Memos und Alarme brauchen keine Kopie.

## Nicht Teil

Entfernen von Area aus Modell, Operationen und Datenbank (spätere Tasks); der Prompt für Claude_Harness (letzte
Task der Story).
