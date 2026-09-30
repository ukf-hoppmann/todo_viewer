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
| `GET /health` | Erreichbarkeit prüfen: `{status: "ok", api: "2"}`, ohne Dateizugriff. |
| `GET /backlog` | Alle Quellen (mit `item_count` und ggf. `problem`) und alle Items. Ohne `config.json` leer. |
| `GET /index?source_id=…` | Schlanke Übersicht aller Items (aktiv und archiviert) mit nur `source_id`, `id`, `type`, `status`, `title`, `parent`, `area` (`null` ohne Area), zum Einordnen neuer Arbeit; optional auf eine Quelle begrenzt. |
| `POST /items` | Legt ein Epic, eine Story oder einen Task an; der Server vergibt die ID. Antwort 201 mit dem neuen Item. |
| `GET /items/{source_id}/{item_id}` | Ein Item per ID, aktiv oder archiviert. |
| `DELETE /items/{source_id}/{item_id}?version=…&cascade=…` | Verschiebt ein Item (mit `cascade=true` samt Nachfahren) in den Papierkorb. |
| `GET /trash?source_id=…` | Items im Papierkorb einer Quelle. |
| `POST /trash/{source_id}/{item_id}/restore` | Holt ein Item samt Nachfahren aus dem Papierkorb (`{version}`). |
| `DELETE /trash/{source_id}/{item_id}?version=…` | Löscht ein Item im Papierkorb samt Nachfahren und Ordnern `items/<ID>/` endgültig. |
| `PATCH /items/{source_id}/{item_id}` | Ändert ein oder mehrere Felder eines Items in einem Schritt. |
| `POST /items/{source_id}/{item_id}/retype` | Ändert den Typ eines Items; es bekommt die nächste freie ID des neuen Typs, alle Verweise im Backlog folgen (`{version, type}`); die Antwort nennt mit `notices` mögliche Verweise außerhalb des Backlogs. |
| `GET /items/{source_id}/{item_id}/documents/{name}` | Notes- oder Spec-Dokument eines Items lesen, mit `version`. |
| `PUT /items/{source_id}/{item_id}/documents/{name}` | Notizen oder Spec mit dem ganzen neuen Text ersetzen oder neu anlegen. |
| `POST /items/{source_id}/{item_id}/notes` | Datierten Notes-Eintrag anhängen. |
| `GET /sources` | Eingetragene Projekte (Markdown und Datenbank) in ihrer Reihenfolge. |
| `POST /sources` | Projekt hinzufügen: Markdown mit `path` (optional `project`; ohne Namen der des Git-Repos), Datenbank mit `backend: "database"` und `project`. |
| `POST /backlogs` | Neuen, leeren Backlog anlegen und als Quelle eintragen. Antwort 201 mit der Quelle. |
| `PUT /sources/{source_id}` | Name, Ordner bzw. `sync_path` und den Spiegel (`mirror`) ändern; mit anderem `backend` wechselt die Primärquelle (nach Sync). |
| `POST /sources/{source_id}/sync` | Überträgt zwischen Primärquelle und Spiegel eines Projekts (Datenbank und Markdown-Ordner), in der gewählten Richtung; erst Vorschau, dann Ausführen (siehe unten). |
| `DELETE /sources/{source_id}` | Projekt austragen. Markdown-Dateien bleiben; ein Datenbank-Projekt mit Items wird abgelehnt. |
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
  - Wieder öffnen: Ein Status ohne Endstatus (z. B. `In progress`) öffnet ein
    abgeschlossenes Epic, eine Story oder einen Task wieder, egal ob es aktiv
    oder archiviert ist; ein archiviertes Item wandert dabei zurück nach
    `TODO.md`, und `Resolution` wird entfernt. Unter einem geschlossenen Parent
    (Completed/Rejected) darf kein aktives Item stehen: Anlegen, Umhängen,
    Wiederöffnen eines Kindes oder Wiederherstellen aus dem Papierkorb
    lehnt der Server dann mit 409 `parent_closed` ab. `details.id` ist das
    betroffene Item, `details.items` nennt die geschlossenen Vorfahren bis zum
    ersten offenen, von oben nach unten; in dieser Reihenfolge wieder öffnen
    und die Änderung wiederholen. Wer dagegen einen Parent mit aktiven
    Kindern schließen will, bekommt `children_still_active`.
  - `POST /items`: `{source_id, type ("Epic"|"Story"|"Task"), title, area,
    goal, completion_criteria, priority?, parent?, required_for_parent?,
    dependencies?, summary?, created?}`. Die ID ist die nächste freie Nummer
    des Typs über aktive und archivierte Items (`STORY-007` usw.); Status ist
    immer `Open`, `priority` standardmäßig `Normal`, `created` standardmäßig
    heute. Mit `parent` ist `required_for_parent` Pflicht. Der Eintrag kommt
    ans Ende des Abschnitts `## Work items` in `TODO.md`. Die Parent-Regeln
    werden wie beim Bearbeiten geprüft.
  - Typwechsel (`POST /items/…/retype`, `{version, type}`; Entscheidung:
    [STORY-007](../todo/items/STORY-007/STORY-007_notes.md)): Der Typ ist das
    Präfix der ID und lässt sich nicht über `PATCH` ändern. Der Server
    vergibt die nächste freie ID des neuen Typs (über aktive, archivierte und
    gelöschte Items) und zieht im selben Schritt nach: Kopfzeile und `Type`
    des Items, `Parent` und `Dependencies` aller Items (auch Archiv und
    Papierkorb), Titel, Summary, Goal, Completion criteria und Resolution, in
    denen die alte ID steht, sowie Inhalt und Dateinamen der Notes und
    Specs; der Ordner `items/<alte ID>/` wird zu `items/<neue ID>/`. Die
    Antwort ist `{item, old_id, notices}`: das Item unter seiner neuen ID, die
    alte ID und eine Liste von Hinweisen `{code, message, details}`. Der
    Hinweis `external_references_may_remain` (`details.old_id`,
    `details.new_id`) sagt, dass Verweise außerhalb des Backlogs
    (Techdocs, Tagesberichte, Code, Commit-Messages) nicht angepasst wurden und
    geprüft werden sollten; die UI übersetzt den `code`, `message` ist
    englisch und für Agenten gedacht. Die Parent-Regeln werden
    vorher geprüft (z. B. ein Epic hat keinen Parent: 409 `epic_with_parent`);
    gleicher oder unbekannter Typ ergibt 400 `invalid_value`, ein Item im
    Papierkorb 409 `item_deleted`. Existiert `items/<neue ID>/` schon, lehnt
    der Server mit 409 `item_folder_exists` ab. Verweise außerhalb des
    Backlogs (Tagesberichte, Commits, Techdocs) und weitere Freitext-Felder
    (`extra_fields`) bleiben unverändert. Schlägt das Schreiben der
    Backlog-Dateien fehl, wird der Ordner zurückbenannt. Fällt nur das
    abschließende Umschreiben eines Dokumenttexts aus, bleibt der Backlog
    konsistent, der Text kann aber noch die alte ID nennen.
  - Löschen geht über den Papierkorb (Entscheidung:
    [STORY-011](../todo/items/STORY-011/STORY-011_notes.md)).
    `DELETE /items/…` markiert das Item mit `Deleted: <Datum>` und verschiebt
    es nach `archive.md` (ohne Archiv bleibt es markiert an seinem Platz).
    Hat es Kinder, antwortet der Server mit 409 `has_children` und nennt sie
    als Warnung; mit `cascade=true` werden alle Nachfahren mitverschoben.
    Abgelehnt mit 409 `item_referenced`, solange Items außerhalb des
    Papierkorbs per Dependency darauf verweisen, und wenn eine Parent-Regel
    bräche (z. B. letztes Pflichtkind eines laufenden Epics). Items im
    Papierkorb erscheinen nicht in `GET /backlog` und `GET /index`, zählen
    nicht für die Parent-Regeln und sind nicht bearbeitbar (409
    `item_deleted`); `GET /items/…` liefert sie mit gesetztem `deleted`.
  - Wiederherstellen (`POST /trash/…/restore`, `{version}`) nimmt die
    Markierung samt Nachfahren zurück; offene Items wandern zurück nach
    `TODO.md`. Abgelehnt, solange der Parent selbst im Papierkorb liegt
    (409 `parent_deleted`) oder eine Parent-Regel bräche. Eigene Altlasten
    des Items (z. B. fehlendes `Required for parent`) blockieren nicht.
  - Endgültig löschen (`DELETE /trash/…?version=…`) geht nur im Papierkorb
    (sonst 409 `item_not_deleted`) und entfernt Eintrag und Nachfahren samt
    ihrer Ordner `items/<ID>/`; abgelehnt, solange andere Items verweisen.
  - Dokumente werden über Item und Namen adressiert (Dateiname wie
    `STORY-003_spec.md`), nie über Pfade. Arbeitsweise zum Ändern: `GET
    …/documents/{name}` holt Text und `version`, `PUT …/documents/{name}` mit
    `{content, version, summary?}` ersetzt den ganzen Text (Notizen wie Specs);
    bei geänderter Version 409 `version_conflict`. `version: null` legt ein
    neues Dokument an: `<ID>_notes.md` für die ersten Notizen (dann ist wie beim
    Anhängen eine Summary nötig) oder `<ID>_spec.md` bzw. `<ID>_spec_<thema>.md`;
    es wird im Feld `Notes` bzw. `Spec` des Items eingetragen.
    Neue Notiz-Einträge hängt `POST …/notes` an:
    `{topic, discussed?, decided?, open?, summary?}`; der Server setzt das
    Datum und schreibt `## <Datum> — <Thema>` mit den Abschnitten
    `### Discussed`/`### Decided`/`### Open`. Der erste Eintrag legt
    `items/<ID>/<ID>_notes.md` an und trägt `Notes` ein; hat das Item noch keine
    Summary, ist `summary` Pflicht.
  - Projekte (`/sources`): `{path?, project?, backend?, sync_path?, mirror?}`.
    `backend` ist `markdown` (Standard beim Anlegen) oder `database`.
    Markdown braucht `path` (Ordner mit `TODO.md`), Datenbank einen Namen
    (`project`, sonst 400 `value_required`); `sync_path` ist der Ordner, mit dem
    ein Datenbank-Projekt seine Markdown-Dateien abgleicht. Beim Ändern darf
    `backend` fehlen. Ein anderer Wert als der gespeicherte stellt das Projekt
    um (Entscheidung: [TASK-003](../todo/items/TASK-003/TASK-003_notes.md)):
    nur wenn beide Seiten gleich sind, sonst 409 `sync_required` und nichts
    ändert sich. Davor sichert der Dienst die bisherige Primärquelle (Ort und
    Inhalt: [Betrieb](operations.md)); scheitert das, gilt 409 `backup_failed`. Vorher also synchronisieren: Markdown → Datenbank mit
    `from_md` (der Sync liest bei einem Markdown-Projekt den Ordner in die
    Datenbank), Datenbank → Markdown mit `to_md`. Beim Umstellen wandert der
    Ordner von `path` nach `sync_path` bzw. zurück; `path` und `sync_path` im
    Aufruf werden dabei nicht gelesen, ein neuer `project`-Name schon. Die
    Markdown-Dateien bleiben liegen. Ein Markdown-Ordner, der schon einem
    anderen Projekt gehört, lehnt 409 `duplicate` ab. `source_id` ist eine
    UUID, die sich weder bei Namens- oder Pfadänderungen noch beim Umstellen
    ändert; die Item-IDs bleiben gleich. Wird ein Markdown-Projekt ausgetragen,
    verschwindet auch die Kopie seiner Items in der Datenbank (ein Datenbank-
    Projekt mit Items wird weiter abgelehnt).
  - Primärquelle und Spiegel (Regel 1 der Architektur, Stand
    STORY-029): `backend` ist
    die Primärquelle, sie hält die Wahrheit. Die andere Seite darf als Spiegel
    geführt werden und wird nur durch einen Sync geschrieben. `mirror` ist
    `none`, `database` oder `markdown`: bei einem Markdown-Projekt schaltet
    `database` die Datenbank-Kopie ein und `none` aus (das Ausschalten löscht
    die Kopie in der Datenbank, nicht die Markdown-Dateien); bei einem
    Datenbank-Projekt braucht `markdown` einen `sync_path` (sonst 400
    `sync_path_missing`), `none` entfernt ihn. Der Spiegel der eigenen Seite
    (`markdown` bei Markdown, `database` bei Datenbank) ergibt 400
    `invalid_value`; fehlt `mirror`, bleibt der Spiegel wie er ist. Beim
    Wechsel der Primärquelle bleibt die bisherige Seite als Spiegel:
    Markdown → Datenbank behält den Ordner als `sync_path`, Datenbank →
    Markdown behält die Kopie in der Datenbank. Ein Projekt aus einer früheren
    Version hat keinen Spiegel, bis man ihn einschaltet.
  - Sync (`POST /sources/{source_id}/sync`,
    `{direction?, confirm?, token?, delete_missing?, language?}`; Entscheidungen:
    [STORY-023](../todo/items/STORY-023/STORY-023_spec.md)): für Projekte mit
    Spiegel (Datenbank-Projekt mit `sync_path`, Markdown-Projekt mit
    Datenbank-Spiegel; ein Markdown-Projekt ohne Spiegel liest nur in die
    Datenbank). `direction` ist `to_md` (Datenbank → Ordner) oder `from_md`
    (Ordner → Datenbank); fehlt sie, gilt die Richtung von der Primärquelle zum
    Spiegel (siehe unten). Übertragen werden `TODO.md`,
    `archive.md`, Papierkorb sowie Notes und Specs (auch Themen-Specs) aller
    Items. Ohne `confirm` ist der Aufruf eine Vorschau und ändert nichts:
    `items` und `documents` mit `created`, `changed` (Ziel wird überschrieben),
    `unchanged` (Anzahl) und `missing` (nur auf dem Ziel vorhanden), dazu
    `skipped` (Dokumente, die der Sync nicht trägt: als Pfad notiert,
    nicht lesbar oder fehlend) und ein `token`, das den Stand beider Seiten
    kennzeichnet. Mit `confirm: true` und diesem `token` wird ausgeführt; hat
    sich seitdem eine Seite geändert (oder fehlt das `token`), antwortet der
    Server mit 409 `sync_stale`. `missing` bleibt auf dem Ziel stehen und
    kommt als `kept` zurück; nur mit `delete_missing: true` wird es gelöscht
    (`deleted`). `language` (`en`, Standard, oder `de`) gilt für neu angelegte
    Markdown-Dateien; ein fehlender Zielordner wird bei `to_md` angelegt. Die
    Markdown-Dateien sind danach normalisiert, nicht byte-gleich zu früheren
    Fassungen; Export → Import → Export ergibt gleiche Dateien und Items mit
    gleicher `version`. Ein Backlog, der nicht lesbar ist, bricht vor jeder
    Änderung ab (400 `sync_source_invalid`, `details.reason` = Grund, etwa
    `not_found`, `unsupported_format`, `parse_error`). Dokumente eines Items
    findet der Sync über dessen Felder `Notes`/`Spec`; Dateien im Ordner
    `items/<ID>/`, die dort nicht stehen, sieht er nicht. Die Richtung wählt
    man je Aufruf; Standard ist von der Primärquelle zum Spiegel (Datenbank-
    Projekt: `to_md`, Markdown-Projekt: `from_md`), die Gegenrichtung
    überschreibt die Primärquelle mit dem Spiegel und zeigt die Vorschau
    genauso. Ein Markdown-Projekt mit Datenbank-Spiegel akzeptiert beide
    Richtungen; ohne Spiegel nur `from_md` (Ordner → Datenbank unter
    derselben `source_id`, das ist der Weg beim Umstellen), `to_md` ergibt 409
    `sync_same_backend`. Das Umstellen der Primärquelle ist `PUT /sources/{id}`
    mit neuem `backend` nach dem Sync (siehe Projekte). Es gibt keinen
    automatischen Sync.
  - `POST /backlogs`: `{path, project?, language?}` mit `language` `en`
    (Standard) oder `de`. Legt den Ordner bei Bedarf an und schreibt
    `TODO.md` und `archive.md` mit Format-Kennung, `## Work items` und
    `No entries.` (wie die Vorlagen des Claude_Harness) sowie den Ordner
    `items/`. Eine vorhandene `archive.md` bleibt unverändert. Abgelehnt mit
    409 `duplicate`, wenn der Ordner schon als Quelle eingetragen ist, und mit
    409 `backlog_exists`, wenn er schon eine `TODO.md` enthält (dann
    `POST /sources` verwenden).
- Ausgabe:
  - Items mit `key` (`<source_id>/<id>`), `source_id`, `id`, `version`,
    `archived`, `deleted` (Datum oder `null`), `project`, den geparsten Feldern, `documents`
    (`[{name, kind: "notes"|"spec"}]`), `extra_fields` für alle weiteren
    Freitext-Felder und `archive_supported`.
  - Dokumente: `{name, kind, content, version}`.
  - Projekte: `{id, project, path, backend, sync_path, primary, markdown_path, mirror}` (`primary` = `backend`;
    `markdown_path` der Markdown-Ordner, egal auf welcher Seite, `null` ohne; `mirror` `none`/`markdown`/`database`); in `GET /backlog`
    zusätzlich `item_count` und `problem`. Bei Datenbank-Projekten ist `path`
    leer.
  - `version` ist ein Hash über den gespeicherten Inhalt des Items und ändert
    sich mit jeder Änderung daran; Änderungen an anderen Items lassen sie
    unverändert.
  - Ein Edit liefert das geänderte Item mit neuer `version` zurück; bei
    `Completed`/`Rejected` ist es danach archiviert, beim Zurücksetzen wieder
    aktiv.
- Fehler: immer `{code, message, details}`.

| HTTP | Codes |
|---|---|
| 400 | `bad_request` (Validierung, auch unbekannte Felder), `sync_path_missing` (Projekt hat keinen `sync_path`), `sync_source_invalid` (Quelle oder Ziel des Syncs nicht lesbar), `invalid_value`, `value_required`, `not_editable`, `resolution_required`, `missing_path`, `not_found`, `not_a_dir`, `no_todo`, `unsupported_format` |
| 403 | `forbidden` (Dokument außerhalb des Backlog-Ordners oder nicht `.md`/`.markdown`/`.txt`) |
| 404 | `source_gone`, `file_not_found`, `item_not_found` |
| 409 | `version_conflict` (Item seit dem Lesen geändert), `file_changed` (Datei zwischen Lesen und Schreiben extern geändert), `duplicate_item` (ID mehrfach im Backlog), `duplicate` (Quelle schon eingetragen), `backlog_exists` (Ordner hat schon eine `TODO.md`), `item_folder_exists` (Typwechsel: `items/<neue ID>/` existiert schon), `project_not_empty` (Datenbank-Projekt mit Items austragen; `details.project`), `sync_required` (Backend per `PUT` umstellen, obwohl die Seiten sich unterscheiden), `backup_failed` (Backend per `PUT` umstellen, aber das Backup der bisherigen Primärquelle schlug fehl; `details.reason`, nichts geändert), `sync_same_backend` (Markdown-Projekt mit `to_md`: Markdown-Projekte lassen sich nur in die Datenbank lesen), `sync_stale` (Sync: eine Seite änderte sich seit der Vorschau) |
| 409 | Regelverstöße des Backlog-Formats, `details.id` = betroffenes Item, `details.items` = auslösende Items: `epic_without_required_child`, `required_children_not_done`, `children_still_active`, `parent_closed`, `epic_with_parent`, `required_for_parent_missing`, `parent_cycle`, `dependency_cycle`, `unknown_reference`, `summary_required_with_notes`, `item_referenced`, `has_children`, `item_deleted`, `item_not_deleted`, `parent_deleted` |
| 500 | `write_failed` (z. B. fehlende Schreibrechte) |

Alle übrigen Pfade liefern das gebaute Frontend aus `web/dist`; fehlt der
Build, antwortet der Server mit 503 und einem Hinweis.

## Nutzung durch Agenten

- Zweck: Agenten (z. B. der `todo`-Skill des Claude_Harness) pflegen Backlogs
  über die HTTP-API statt die Dateien direkt zu bearbeiten.
- Aufruf / Endpunkt: Der Container läuft dauerhaft (`restart: unless-stopped`)
  und ist nur lokal erreichbar: `http://localhost:5411/api/v2`
  (gleichwertig `http://todo.localhost:5411/api/v2`). Ob er läuft, zeigt
  `GET /health`; wie ein Agent reagiert, wenn nicht, regelt das Harness
  (Entscheidung: [STORY-010](../todo/items/STORY-010/STORY-010_notes.md)).
- Eingabe: Die `source_id` eines Projekts steht in `GET /sources` beim Eintrag,
  dessen `path` der Backlog-Ordner ist (z. B. `<repo>/docs/todo`); sie ist eine
  UUID und nicht aus dem Pfad ableitbar, also jedes Mal dort nachschlagen. Fehlt er,
  legt `POST /sources` mit `{path}` ihn an; gibt es noch keinen Backlog,
  erzeugt `POST /backlogs` mit `{path, language?}` die Dateien und trägt die
  Quelle ein. So entsteht die `TODO.md` immer im lesbaren Format. Ein
  typischer Durchlauf:

  1. Überblick: `GET /index?source_id=…` (nur ID, Typ, Status, Titel, Parent, Area).
  2. Einzelnes Item samt `version`: `GET /items/{source_id}/{id}`.
  3. Anlegen: `POST /items` mit `{source_id, type, title, area, goal,
     completion_criteria, …}`.
  4. Ändern: `PATCH /items/{source_id}/{id}` mit `{version, fields: {…}}`,
     z. B. `{"status": "In progress"}` oder `{"parent": "EPIC-001",
     "required_for_parent": "Yes"}`.
  5. Wieder öffnen: ebenfalls `PATCH` mit `{"status": "In progress"}`, für
     Epics, Stories und Tasks, auch archivierte. Antwortet der Server beim
     Anlegen oder Ändern mit 409 `parent_closed`, stehen die geschlossenen
     Vorfahren in `details.items` (von oben nach unten): nach Rückfrage beim
     Projekteigner einzeln wieder öffnen, dann die Änderung wiederholen.
  6. Notizen: neuer Eintrag per `POST /items/{source_id}/{id}/notes` mit
     `{topic, discussed, decided, open, summary?}`; Notizen und Specs ändern:
     `GET …/documents/{name}` holen, `PUT …/documents/{name}` mit
     `{content, version}` zurückschreiben.
  7. Typ ändern: `POST /items/{source_id}/{id}/retype` mit `{version, type}`;
     das Item hat danach eine neue ID (`item.id`). `notices` nennt, was der
     Server nicht anpassen kann (`external_references_may_remain`): auf
     Anfrage des Projekteigners nach der alten ID (`old_id`) in Techdocs,
     Tagesberichten und Code suchen und sie durch die neue ersetzen.
  8. Löschen: `DELETE /items/{source_id}/{id}?version=…` (Papierkorb; bei
     Kindern erst Warnung, dann mit `cascade=true`); wiederherstellen oder
     endgültig löschen über `/trash`.
- Ausgabe: wie bei der HTTP-API oben; jede Änderung liefert den neuen Stand
  mit neuer `version`.
- Fehler: Bei `version_conflict` (409) das Item neu lesen und die Änderung
  prüfen, nicht blind wiederholen. Regelverstöße (409) nennen in
  `details.items` die blockierenden Items. Die Parent-Regeln des
  Backlog-Formats prüft der Server; der Agent muss sie nicht selbst
  durchsetzen.

## Dateiformat: Backlog-Ordner

- Zweck: Quelle der angezeigten Items.
- Aufruf / Endpunkt: ein Ordner mit `TODO.md`; `archive.md` im selben Ordner
  wird mitgelesen; `Notes`/`Spec` verweisen auf Dateien unter `items/<ID>/`.
- Eingabe: Claude_Harness-Backlog-Format (Version 1/2); die Datei muss die
  Format-Kennung enthalten (z. B. „backlog format version 2“,
  „Backlog-Format Version 1“ oder „Backlogformat Version 1“). Jeder Eintrag hat eine ID, die im Backlog
  (`TODO.md` und `archive.md` zusammen) eindeutig ist. Einfache Checklisten
  ohne IDs werden nicht unterstützt und als Problem `unsupported_format`
  gemeldet.
  Alte deutsche Prioritäten (`Dringend`, `Wichtig`, `Perspektivisch`) werden
  als `Urgent`, `Important`, `Prospective` gelesen.
  Erweiterung des Viewers gegenüber dem Claude_Harness-Format: Items im
  Papierkorb tragen das Feld `Deleted: <YYYY-MM-DD>.` und liegen in
  `archive.md`, auch wenn ihr Status nicht abgeschlossen ist. Der
  Backlog-Check des Harness kennt das Feld noch nicht und meldet solche
  Einträge als Fehler.
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
