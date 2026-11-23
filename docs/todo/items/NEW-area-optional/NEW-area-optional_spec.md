# NEW-area-optional — Spec: Area beim Anlegen nicht mehr Pflicht

Zu `STORY-106`. Erster Schritt der Entfernung von Area: Server und Oberfläche müssen sich getrennt umbauen lassen.
Diese Task öffnet den Server; die Oberfläche folgt, danach entfernt eine Task das Feld ganz.

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.

## Umfang

- `server/src/viewer/plugins/backlog/domain/editing.py`: `REQUIRED_TEXT` enthält `"area"` (Zeile ~29) und die
  Pflichtprüfung in `build_new_item` (Schleife über `("title", "area", "goal", "completion_criteria")`, ~160);
  `area=str(values["area"])` (~174) wird `None`, wenn nichts gegeben ist. Beim Ändern bleibt `area` ein
  editierbares Feld (`FIELDS`), nur ohne Pflicht.
- `server/src/viewer/plugins/backlog/application/operations.py`: Texte von `CreateItem` (Kommentar „Pflicht“) und
  der Operation `create_item` („Pflicht: title, area, goal, completion_criteria“).
- `server/src/viewer/plugins/memos/application/conversion.py` (`promotion_fields`, Docstring von `promote`) und
  `memos/application/operations.py` (Kommentar zu `PromoteMemo.fields`, Beschreibung der Operation
  `promote_memo`): `area` ist keine Pflicht.
- Nicht ändern: Index-Zeilen, `list_areas`, Spiegel, Datenbank.

## Tests

- `tests/implementation/unit/server/plugins/backlog/domain/test_editing.py`: Pflichtfelder ohne Area.
- `tests/implementation/integration/server/plugins/backlog/test_item_editing.py`: Item ohne Area anlegen, mit Area
  weiter möglich.
- `tests/implementation/integration/server/plugins/memos/test_memo_conversion.py`: Beförderung ohne Area.
- Die generierten Typen (`client/src/shared/api/schema.d.ts`) ändern sich nur, wenn sich das OpenAPI-Schema
  ändert; `scripts/gen-api.sh` ausführen und die Datei einchecken, falls `test_openapi_types.py` es verlangt.
