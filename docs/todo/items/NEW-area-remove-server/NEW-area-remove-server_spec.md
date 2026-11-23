# NEW-area-remove-server — Spec: Area aus Server und Datenbank entfernen

Zu `STORY-106`. Voraussetzungen: der Spiegel schreibt kein Area mehr und liest es ignorierend (Task „Backlog-Spiegel:
Format Version 3“), die Oberfläche benutzt es nicht mehr (Task „Oberfläche ohne Area“).

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.

## Umfang

- Domain (`server/src/viewer/plugins/backlog/domain/`): `model.py` (`Item.area`), `editing.py` (`FIELDS`,
  `REQUIRED_TEXT`, `apply_update`, `build_new_item`).
- Anwendung (`application/operations.py`): `IndexItem.area`, `ItemOut.area`, `ListAreas` mit Operation
  `list_areas`, `INDEX_HEADER` und die Zeilen `{e.area or '-'}`, Beschreibungen. Index-Kopf neu:
  `ID | Type | Status | Title | Parent | Notes`.
- Datenbank (`infrastructure/database/repository.py`): `a.name AS area`, `_area_uid`, `area_uid` in INSERT und
  UPDATE; `schema.py`: neue Migration (nach `_v4`, Version 5), die `area_uid` aus `backlog_items` und die Tabelle
  `backlog_areas` entfernt. Prüfen, ob `ALTER TABLE … DROP COLUMN` an der Spalte mit Fremdschlüssel scheitert (in
  SQLite tut es das für Spalten mit `REFERENCES`); wenn ja, die Tabelle neu aufbauen (neue Tabelle, `INSERT … SELECT`,
  alte löschen, umbenennen, Indizes neu anlegen), ohne die Fremdschlüssel anderer Tabellen auf `backlog_items`
  (`backlog_dependencies`, `backlog_trashed_documents`, …) zu verlieren. Das Backup vor der Migration macht die
  Kern-Infrastruktur.
- Mirror-Teilnehmer: Reste von `area` in `infrastructure/mirror/participant.py` entfernen (die Task zu Version 3 hat
  Laden und Schreiben schon abgeschaltet).
- Memos (`plugins/memos/application/conversion.py`, `operations.py`): `area` aus den Beschreibungen und aus den
  Feldern der Beförderung.
- Import aus dem alten Viewer (`server/src/viewer/app/import_legacy/writer.py`, `legacy_schema.py`): den Bereich der
  alten Items weder lesen noch schreiben müssen; ein alter Bestand mit Bereichen importiert fehlerfrei.
- Generierte Typen: `scripts/gen-api.sh` ausführen, `client/src/shared/api/schema.d.ts` einchecken; der Test
  `tests/implementation/integration/server/test_openapi_types.py` prüft es.
- Test-Helfer: `tests/helpers/server/backlog_fixtures.py`, `memos_api.py`, `legacy_db.py` (der Helfer für die alte
  Datenbank darf Area weiter erzeugen: sie gehört zum alten Format).
- Tests anpassen: `tests/implementation/unit/server/plugins/backlog/domain/test_editing.py`; Integration unter
  `tests/implementation/integration/server/plugins/` (`backlog/`, `memos/`, `alarms/`, `mindmap/`,
  `test_element_state.py`) und `…/app/test_import_legacy.py`; das System-Skript des Harness
  (`tests/implementation/system/server/test_harness_flow.py`).
- Doku: `docs/techdocs/interfaces.md` (MCP-Tabelle, Index-Zeilen, `backlog_list_areas`), `docs/techdocs/neubau-server.md`
  (Tabellen, Schreiben, Spiegel, Beförderung, Import), `README.md`; die Beschreibung der Mindmap in
  `docs/todo/items/EPIC-008/EPIC-008_spec.md` bleibt (sie spricht schon vom Ersatz).

## Regeln

- Kein abgeleiteter Ersatzwert (Entscheidung `STORY-106`): wo Area stand, gibt es nichts, das Thema kommt aus dem
  Knoten der Mindmap.
- Die Migration verliert keine Items, Abhängigkeiten, Dokumente oder Papierkorb-Zustände; nur die Area-Werte gehen.

## Nicht Teil

Der Prompt für die KI und für Claude_Harness (nächste Task).
