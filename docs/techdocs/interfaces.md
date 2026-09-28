# Schnittstellen

<!-- Nur öffentliche Schnittstellen: API, CLI, Dateiformate, Hooks, Ereignisse. -->

Das vollständige Schema der HTTP-API liegt in `web/src/api/openapi.json`
(erzeugt mit `backend/scripts/export_openapi.py`).

## HTTP-API v2

- Zweck: Lesen und Bearbeiten der konfigurierten Backlogs, Verwaltung der
  Quellen, UI-Zustand.
- Aufruf / Endpunkt: Präfix `/api/v2`, Standard-Port 5411.

| Methode und Pfad | Zweck |
|---|---|
| `GET /backlog` | Alle Quellen (mit `item_count` und ggf. `problem`) und alle Items. Ohne `config.json` leer. |
| `GET /index?source_id=…` | Schlanke Übersicht aller Items (aktiv und archiviert) mit nur `source_id`, `id`, `type`, `status`, `title`, `parent`, zum Einordnen neuer Arbeit; optional auf eine Quelle begrenzt. |
| `POST /items` | Legt ein Epic, eine Story oder einen Task an; der Server vergibt die ID. Antwort 201 mit dem neuen Item. |
| `GET /items/{source_id}/{item_id}` | Ein Item per ID, aktiv oder archiviert. |
| `PATCH /items/{source_id}/{item_id}` | Ändert ein oder mehrere Felder eines Items in einem Schritt. |
| `GET /items/{source_id}/{item_id}/documents/{name}` | Notes- oder Spec-Dokument eines Items lesen, mit `version`. |
| `PUT /items/{source_id}/{item_id}/documents/{name}` | Spec ersetzen oder neu anlegen. |
| `POST /items/{source_id}/{item_id}/notes` | Datierten Notes-Eintrag anhängen. |
| `GET /sources` | Konfigurierte Quellen. |
| `POST /sources` | Quelle hinzufügen (`path`, optional `project`; ohne Namen der des Git-Repos). |
| `PUT /sources/{source_id}` | Quelle ändern. |
| `DELETE /sources/{source_id}` | Quelle entfernen. |
| `GET /folders?path=…` | Unterordner für den Ordner-Browser, mit Markierung, ob eine `TODO.md` enthalten ist. |
| `GET /ui-state`, `PUT /ui-state` | UI-Zustand lesen bzw. vollständig ersetzen (freies JSON-Objekt). |

- Eingabe:
  - Items werden nur über `source_id` und ihre ID adressiert; Datei, Zeile
    und Ablageort (aktiv/Archiv) gehören nicht zum Vertrag. So kann der
    Speicher später ausgetauscht werden (Entscheidung:
    [EPIC-001](../todo/items/EPIC-001/EPIC-001_notes.md)).
  - `PATCH /items/{source_id}/{item_id}`: `{version, fields, resolution?}`.
    `version` ist Pflicht und muss der zuletzt gelesenen Version entsprechen;
    `resolution` ist Pflicht bei `Completed`/`Rejected`. `fields` enthält nur
    die zu ändernden Felder: `title`, `status`, `priority`,
    `required_for_parent` (`Yes`/`No`), `goal`, `completion_criteria`,
    `summary`, `area`, `parent`, `dependencies` (Liste von IDs). `null`
    entfernt `summary` bzw. `parent` (mit `parent` fällt auch
    `required_for_parent` weg); Titel, Priorität, Goal, Completion criteria und
    Area dürfen nicht leer werden. Unbekannte Felder werden abgelehnt. Alle
    Felder werden zusammen geprüft und geschrieben, z. B. `parent` zusammen
    mit `required_for_parent`. Texte werden auf eine logische Zeile
    zusammengezogen und in der Datei mit vier Leerzeichen Einzug umbrochen.
    Der Server prüft die Parent-Regeln des Backlog-Formats und lehnt eine
    Änderung ab, wenn sie einen neuen Regelverstoß erzeugt; bereits
    bestehende Verstöße blockieren andere Änderungen nicht (Entscheidung:
    [STORY-005](../todo/items/STORY-005/STORY-005_notes.md)).
  - `POST /items`: `{source_id, type ("Epic"|"Story"|"Task"), title, area,
    goal, completion_criteria, priority?, parent?, required_for_parent?,
    dependencies?, summary?, created?}`. Die ID ist die nächste freie Nummer
    des Typs über aktive und archivierte Items (`STORY-007` usw.); Status ist
    immer `Open`, `priority` standardmäßig `Normal`, `created` standardmäßig
    heute. Mit `parent` ist `required_for_parent` Pflicht. Der Eintrag kommt
    ans Ende des Abschnitts `## Work items` in `TODO.md`. Die Parent-Regeln
    werden wie beim Bearbeiten geprüft.
  - Dokumente werden über Item und Namen adressiert (Dateiname wie
    `STORY-003_spec.md`), nie über Pfade. `PUT …/documents/{name}`:
    `{content, version}`; `version` ist die zuletzt gelesene Version, `null`
    legt eine neue Spec an. Neue Specs heißen `<ID>_spec.md` oder
    `<ID>_spec_<thema>.md` und werden im Feld `Spec` des Items eingetragen.
    Notes sind nur per `POST …/notes` erweiterbar:
    `{topic, discussed?, decided?, open?, summary?}`; der Server setzt das
    Datum und schreibt `## <Datum> — <Thema>` mit den Abschnitten
    `### Discussed`/`### Decided`/`### Open`. Der erste Eintrag legt
    `items/<ID>/<ID>_notes.md` an und trägt `Notes` ein; hat das Item noch keine
    Summary, ist `summary` Pflicht.
  - Quellen: `{path, project?}`; `source_id` ist eine stabile, pfadbasierte ID.
- Ausgabe:
  - Items mit `key` (`<source_id>/<id>`), `source_id`, `id`, `version`,
    `archived`, `project`, den geparsten Feldern, `documents`
    (`[{name, kind: "notes"|"spec"}]`), `extra_fields` für alle weiteren
    Freitext-Felder und `archive_supported`.
  - Dokumente: `{name, kind, content, version}`.
  - `version` ist ein Hash über den gespeicherten Inhalt des Items und ändert
    sich mit jeder Änderung daran; Änderungen an anderen Items lassen sie
    unverändert.
  - Ein Edit liefert das geänderte Item mit neuer `version` zurück; bei
    `Completed`/`Rejected` ist es danach archiviert, beim Zurücksetzen wieder
    aktiv.
- Fehler: immer `{code, message, details}`.

| HTTP | Codes |
|---|---|
| 400 | `bad_request` (Validierung, auch unbekannte Felder), `invalid_value`, `value_required`, `not_editable`, `resolution_required`, `missing_path`, `not_found`, `not_a_dir`, `no_todo`, `unsupported_format` |
| 403 | `forbidden` (Dokument außerhalb des Backlog-Ordners oder nicht `.md`/`.markdown`/`.txt`) |
| 404 | `source_gone`, `config_missing`, `file_not_found`, `item_not_found` |
| 409 | `version_conflict` (Item seit dem Lesen geändert), `file_changed` (Datei zwischen Lesen und Schreiben extern geändert), `duplicate_item` (ID mehrfach im Backlog), `duplicate` (Quelle schon eingetragen) |
| 409 | Regelverstöße des Backlog-Formats, `details.id` = betroffenes Item, `details.items` = auslösende Items: `epic_without_required_child`, `required_children_not_done`, `children_still_active`, `epic_with_parent`, `required_for_parent_missing`, `parent_cycle`, `dependency_cycle`, `unknown_reference`, `summary_required_with_notes` |
| 500 | `write_failed` (z. B. fehlende Schreibrechte) |

Alle übrigen Pfade liefern das gebaute Frontend aus `web/dist`; fehlt der
Build, antwortet der Server mit 503 und einem Hinweis.

## Dateiformat: Backlog-Ordner

- Zweck: Quelle der angezeigten Items.
- Aufruf / Endpunkt: ein Ordner mit `TODO.md`; `archive.md` im selben Ordner
  wird mitgelesen; `Notes`/`Spec` verweisen auf Dateien unter `items/<ID>/`.
- Eingabe: Claude_Harness-Backlog-Format (Version 1/2); die Datei muss die
  Format-Kennung enthalten (z. B. „backlog format version 2“ oder
  „Backlog-Format Version 1“). Jeder Eintrag hat eine ID, die im Backlog
  (`TODO.md` und `archive.md` zusammen) eindeutig ist. Einfache Checklisten
  ohne IDs werden nicht unterstützt und als Problem `unsupported_format`
  gemeldet.
  Alte deutsche Prioritäten (`Dringend`, `Wichtig`, `Perspektivisch`) werden
  als `Urgent`, `Important`, `Prospective` gelesen.
- Ausgabe: Bearbeitungen ändern nur das betroffene Feld bzw. verschieben den
  Eintrag zwischen `TODO.md` und `archive.md`. Geschrieben wird atomar
  (temporäre Datei + Umbenennen); Zeilenenden (LF/CRLF) bleiben erhalten.
- Fehler: siehe `version_conflict`, `file_changed`, `duplicate_item`. Nicht lesbare Quellen erscheinen
  mit `problem` in `GET /backlog`.

## CLI: `todo.sh`

- Zweck: Steuerung des Docker-Containers.
- Aufruf / Endpunkt: `./todo.sh <start|stop|restart|down|update|logs|status|open>`.
- Eingabe: Befehlsname.
- Ausgabe: siehe [README](../../README.md#quickstart-docker).
- Fehler: unbekannter Befehl → Hilfetext, Exit-Code 1.
