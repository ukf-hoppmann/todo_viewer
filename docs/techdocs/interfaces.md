# Schnittstellen

<!-- Nur öffentliche Schnittstellen: API, CLI, Dateiformate, Hooks, Ereignisse. -->

Das vollständige Schema der HTTP-API liegt in `src_old/web/src/api/openapi.json`
(erzeugt mit `src_old/backend/scripts/export_openapi.py`).

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
| `GET /sources/{source_id}/sync-status`, `GET /sync-status` | Welche Seite eines Projekts mit Spiegel sich seit dem letzten Sync geändert hat (siehe unten); rechnet erst beim Aufruf. |
| `GET /storage` | Typ (`kind`), Ort (`location`, ohne Passwort) und Schema-Version der zentralen Datenbank, nur lesend. Ändern lässt sich der Ort nur in `configs/config.json`. |
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
    `sync_path_missing`), `none` schaltet ihn aus und behält den mitgeschickten
    `sync_path`, sodass `markdown` ohne neuen Ordner wieder einschaltet; der Ordner
    verschwindet nur, wenn `sync_path` leer geschickt wird (`markdown_path` bleibt
    bei ausgeschaltetem Spiegel gesetzt, `mirror` ist dann `none`, Status und
    Sync-Schaltflächen verhalten sich wie ohne Spiegel). Der Spiegel der eigenen Seite
    (`markdown` bei Markdown, `database` bei Datenbank) ergibt 400
    `invalid_value`; fehlt `mirror`, bleibt der Spiegel wie er ist. Beim
    Wechsel der Primärquelle bleibt die bisherige Seite als Spiegel:
    Markdown → Datenbank behält den Ordner als `sync_path`, Datenbank →
    Markdown behält die Kopie in der Datenbank. Ein Projekt aus einer früheren
    Version hat keinen Spiegel, bis man ihn einschaltet.
  - Sync (`POST /sources/{source_id}/sync`,
    `{direction?, confirm?, token?, resolutions?, language?}`; Entscheidungen:
    [STORY-023](../todo/items/STORY-023/STORY-023_spec.md),
    [STORY-057](../todo/items/STORY-057/STORY-057_spec.md)): für Projekte mit
    Spiegel (Datenbank-Projekt mit `sync_path`, Markdown-Projekt mit
    Datenbank-Spiegel; ein Markdown-Projekt ohne Spiegel liest nur in die
    Datenbank). Der Abgleich läuft **pro Eintrag** und beidseitig: ein Item oder
    Dokument, das nur in der Datenbank geändert oder neu ist, geht in den Ordner,
    eines, das nur im Ordner geändert oder neu ist, in die Datenbank. Dafür
    speichert der Dienst je Eintrag die Version nach dem letzten Sync (Tabelle
    `sync_entries`, nur Versionen). Übertragen werden `TODO.md`, `archive.md`,
    Papierkorb sowie Notes und Specs (auch Themen-Specs) aller Items. Ohne
    `confirm` ist der Aufruf eine Vorschau und ändert nichts: `items` und
    `documents` mit `created` und `changed` (je Eintrag `origin`: `database` oder
    `markdown`, die Seite, deren Fassung übertragen wird) und `unchanged`
    (Anzahl); `conflicts` mit je `kind` (`item`, `document`, `topic`, `note`, `note_document`), `label`, `name`,
    `reason` (`both_changed`: seit dem letzten Sync auf beiden Seiten geändert,
    `both_new`: auf beiden Seiten neu mit verschiedenem Inhalt,
    `database_deleted`/`markdown_deleted`: auf dieser Seite seit dem letzten Sync
    gelöscht) und beiden Fassungen `database`/`markdown` (Item: `fields` als Liste
    aus `name` und `value`; Dokument: `text`; `null`, wenn der Eintrag auf der
    Seite fehlt); dazu `skipped` (Dokumente, die der Sync nicht trägt: als Pfad
    notiert, nicht lesbar oder fehlend) und ein `token`, das den Stand beider
    Seiten und des gespeicherten Syncstands kennzeichnet. Ohne gespeicherten Stand
    (vor dem ersten Sync) gilt: nur auf einer Seite vorhanden = dort neu; auf
    beiden Seiten verschieden = Konflikt. Mit `confirm: true` und diesem `token`
    wird ausgeführt; hat sich seitdem eine Seite oder der Syncstand geändert (oder
    fehlt das `token`), antwortet der Server mit 409 `sync_stale`. Ein
    **Konflikt wird nie überschrieben oder gelöscht**: `resolutions` ist eine
    Liste aus `{kind, label, name?, choice}` mit `choice` `database` (der Zustand
    der Datenbank gilt: ihre Fassung geht in den Ordner; fehlt der Eintrag in der
    Datenbank, wird er im Ordner gelöscht), `markdown` (der Zustand des Ordners
    gilt, entsprechend: fehlt der Eintrag im Ordner, wird er in der Datenbank
    gelöscht) oder `defer`. Ohne Entscheidung gilt `defer`: der
    Konflikt bleibt auf beiden Seiten und im gespeicherten Stand unverändert und
    wird beim nächsten Abgleich wieder gemeldet; macht man beide Seiten von
    Hand gleich, ist er keiner mehr. Die Antwort mit `confirm` nennt `resolved`
    (übertragen, mit `origin`), `deleted` (durch Entscheidung gelöscht), `deferred`
    (offen gebliebene Konflikte) und `kept` (davon die Löschungen: der Eintrag
    bleibt, wo er ist). `direction` (`to_md` oder `from_md`) ist optional und
    schränkt nur ein, welche Seite der Lauf schreibt (`to_md` nur den Ordner,
    `from_md` nur die Datenbank); ohne Angabe läuft der Abgleich in beide
    Richtungen. Eine Entscheidung, die eine ausgeschlossene Seite schreiben würde,
    bleibt aufgeschoben. `delete_missing` gibt es nicht mehr (400 `bad_request`):
    gelöscht wird nur durch die Entscheidung eines Konflikts. Wer ein
    Item löscht, auf das andere Items verweisen, bekommt von der Seite, die
    das prüft, einen Fehler (z. B. 409 `lifecycle_violation`); der Lauf bricht dann ab, die
    Datenbank wird zuerst und in einer Transaktion geschrieben. Vor einem Lauf, der in die Datenbank schreibt,
    legt der Dienst ein Backup an (409 `database_backup_failed`, wenn das scheitert). `language`
    (`en`, Standard, oder `de`) gilt für neu angelegte Markdown-Dateien; ein
    fehlender Zielordner wird angelegt, wo die Ordnerseite Ziel sein darf (ohne
    `direction` bei einem Datenbank-Projekt, bei `to_md`). Die Markdown-Dateien sind danach
    normalisiert, nicht byte-gleich zu früheren Fassungen; Export → Import →
    Export ergibt gleiche Dateien und Items mit gleicher `version`. Ein Backlog,
    der nicht lesbar ist, bricht vor jeder Änderung ab (400 `sync_source_invalid`,
    `details.reason` = Grund, etwa `not_found`, `unsupported_format`,
    `parse_error`). Dokumente eines Items findet der Sync über dessen Felder
    `Notes`/`Spec`; Dateien im Ordner `items/<ID>/`, die dort nicht stehen, sieht
    er nicht. Ein Markdown-Projekt mit Datenbank-Spiegel akzeptiert alle
    Angaben; ohne Spiegel läuft nur `from_md` (Ordner → Datenbank unter derselben
    `source_id`, das ist der Weg beim Umstellen), `to_md` ergibt 409
    `sync_same_backend`. Das Umstellen der Primärquelle ist `PUT /sources/{id}`
    mit neuem `backend` nach dem Sync (siehe Projekte). Der automatische Sync
    (STORY-059) startet diesen Abgleich selbst für Projekte, deren Besitzer
    `auto_sync` eingeschaltet hat (`PUT /sources/{id}` mit `auto_sync: true`,
    Standard aus, braucht einen Spiegel sonst 400 `auto_sync_needs_mirror`;
    `GET /sources` meldet `auto_sync`): er überträgt nur Konfliktfreies, löscht
    nie, liest keine Dateien mit Git-Merge-Markern (das Projekt pausiert mit
    `auto_paused` = `merge_markers`) und keinen fehlenden Ordner und wartet ab, bis
    sich der Stand zwischen zwei Prüfungen nicht mehr ändert (Abstand
    `AUTO_SYNC_INTERVAL`, siehe [Konfiguration](configuration.md)).
  - Sync-Status (`GET /sources/{source_id}/sync-status`, für alle Projekte
    `GET /sync-status`): `{source_id, state, last_sync_at, conflicts, auto_sync, auto_last_run_at, auto_paused}`
    (die letzten drei beschreiben den Auto-Sync: `auto_sync` = er wirkt für dieses Projekt,
    `auto_last_run_at` = wann er zuletzt etwas übertragen hat, `auto_paused` = Grund,
    warum die letzte Prüfung nicht laufen konnte; beide nur im Speicher seit dem Start). `conflicts` zählt die Einträge,
    die eine Entscheidung brauchen (beide Seiten geändert, auf beiden neu mit
    verschiedenem Inhalt, auf einer Seite gelöscht); `state` ist dann
    `conflicts`, egal welche Seite sich bewegt hat. Sonst sagt `state`, welche
    Seite sich seit dem letzten Sync über diese API bewegt hat: `none` (kein
    Spiegel), `in_sync`, `mirror_changed` (z. B. eine KI hat die
    Markdown-Dateien bearbeitet), `primary_changed`, `both_changed`. Dazu
    `unknown` (nie synchronisiert und die Seiten unterscheiden sich; gleiche
    Seiten gelten als `in_sync`) und `unreadable` (eine Seite ist nicht
    lesbar, die Anfrage scheitert deshalb nicht). `last_sync_at` ist die Zeit
    des letzten Syncs mit `confirm` (ISO 8601), `null` ohne. Verglichen wird der
    Inhalt aller Items und Dokumente beider Seiten; was ein Sync absichtlich
    stehen ließ (aufgeschobene Konflikte), zählt nicht als Änderung. Der Status wird erst beim
    Aufruf berechnet (er liest beide Seiten) und steht nicht in den Listen der
    Projekte (`GET /sources`, `GET /backlog`); das Lesen ändert und
    synchronisiert nichts. Ändert man Ordner oder Spiegel eines Projekts oder
    wechselt die Primärquelle, beginnt der Status wieder bei `unknown` bzw.
    `in_sync`.
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
| 409 | `version_conflict` (Item seit dem Lesen geändert), `file_changed` (Datei zwischen Lesen und Schreiben extern geändert), `duplicate_item` (ID mehrfach im Backlog), `duplicate` (Quelle schon eingetragen), `backlog_exists` (Ordner hat schon eine `TODO.md`), `item_folder_exists` (Typwechsel: `items/<neue ID>/` existiert schon), `project_not_empty` (Datenbank-Projekt mit Items austragen; `details.project`), `sync_required` (Backend per `PUT` umstellen, obwohl die Seiten sich unterscheiden), `backup_failed` (Backend per `PUT` umstellen, aber das Backup der bisherigen Primärquelle schlug fehl; `details.reason`, nichts geändert), `sync_same_backend` (Markdown-Projekt mit `to_md`: Markdown-Projekte lassen sich nur in die Datenbank lesen), `sync_stale` (Sync: eine Seite oder der gespeicherte Syncstand änderte sich seit der Vorschau), `mirror_conflict` (Notes-Sync: eine Datei im Ordner `notes/` änderte sich zwischen Lesen und Schreiben), `auto_sync_needs_mirror` (400: Auto-Sync einschalten ohne Spiegel), `database_backup_failed` (die automatische Sicherung der Datenbank vor einem Sync oder einer Migration schlug fehl; `details.reason`, nichts geändert) |
| 409 | Regelverstöße des Backlog-Formats, `details.id` = betroffenes Item, `details.items` = auslösende Items: `epic_without_required_child`, `required_children_not_done`, `children_still_active`, `parent_closed`, `epic_with_parent`, `required_for_parent_missing`, `parent_cycle`, `dependency_cycle`, `unknown_reference`, `summary_required_with_notes`, `item_referenced`, `has_children`, `item_deleted`, `item_not_deleted`, `parent_deleted` |
| 500 | `write_failed` (z. B. fehlende Schreibrechte) |

Alle übrigen Pfade liefern das gebaute Frontend aus `src_old/web/dist`; fehlt der
Build, antwortet der Server mit 503 und einem Hinweis.

## HTTP-API v2: Topics, Notes und Links

- Zweck: Topics, Notes (Gedanken mit Wiedervorlage), ihre Links und Auslöser
  lesen und bearbeiten. Die Daten liegen immer in der zentralen Datenbank,
  egal welche Primärquelle das Projekt hat (Entscheidung:
  [STORY-039](../todo/items/STORY-039/STORY-039_notes.md)).
- Aufruf / Endpunkt: Präfix `/api/v2`. Topics und Notes werden über den
  **Projektnamen** (`project`, nicht die `source_id`) und ihr Label adressiert
  (`TOPIC-001`, `NOTE-001`); Labels zählen je Projekt und Typ und werden nie
  wiederverwendet. Pfade unterhalb von `/projects/{project}`:

| Methode und Pfad | Zweck |
|---|---|
| `GET /topics?include_deleted=…`, `POST /topics` | Topics lesen bzw. anlegen (`{name, parent?, due_at?}`, 201). |
| `GET /topics/{label}`, `PATCH /topics/{label}` | Ein Topic lesen; umbenennen und Termin setzen (`{name?, due_at?}`, `due_at: null` entfernt den Termin). |
| `POST /topics/{label}/move` | Mit allen Unter-Topics unter `{parent}` verschieben (`null`: nach oben). |
| `DELETE /topics/{label}?cascade=…`, `POST /topics/{label}/restore` | Topic in den Papierkorb bzw. zurück; Antwort ist der Papierkorb `{topics, notes}`. Mit Inhalt nur mit `cascade=true`. |
| `POST /notes` | Note anlegen (`{summary, body?, topic?, review_at?, trigger_mode?}`, 201). |
| `GET /notes/{label}`, `PATCH /notes/{label}` | Eine Note mit Auslösern und abgeleitetem Zustand lesen (auch archivierte und gelöschte); ändern (`{version, summary?, body?, topic?, review_at?, trigger_mode?}`, `null` leert `body`, `topic`, `review_at`). |
| `POST /notes/{label}/keep` | „Behalten“: nur das Prüf-Datum rückt vor (`{version}`). |
| `POST /notes/{label}/move` | Projektwechsel (`{version, project, topic?}`): die Note entsteht im Zielprojekt mit neuem Label, die alte kommt in den Papierkorb; Antwort ist die neue Note. |
| `POST /notes/{label}/triggers`, `DELETE /notes/{label}/triggers/{id}` | Auslöser anlegen (`{kind: time\|event\|topic_due, at?, target?, target_project?, target_status?}`, 201) bzw. entfernen; Antwort ist die Note. |
| `POST /notes/{label}/finish` | Erledigen oder verwerfen (`{version, status: done\|dropped}`); die Note geht ins Archiv. |
| `POST /notes/{label}/snooze` | Zurückstellen (`{version, review_at?, trigger?}`): wieder wartend, gefeuerte Auslöser zurückgesetzt, ein neuer `trigger` ersetzt alle alten. |
| `DELETE /notes/{label}`, `POST /notes/{label}/restore` | Note in den Papierkorb; aus Archiv oder Papierkorb wieder wartend mit neuem Prüf-Datum. |
| `GET /trash` | Topics und Notes des Projekts im Papierkorb. Endgültiges Löschen gibt es über HTTP nicht. |
| `GET /notes/{label}/links`, `POST /notes/{label}/links`, `DELETE /notes/{label}/links/{id}` | Links einer Note lesen; setzen (`{kind: item\|topic\|note, target, target_project?, role?: reference\|origin}`, 201); lösen (Antwort: übrige Links). |
| `GET /items/{label}/notes`, `GET /topics/{label}/notes`, `GET /notes/{label}/backlinks` | Rückwärts: Notes (aller Projekte, ohne Papierkorb), die auf das Item, Topic oder die Note zeigen, mit `{project, label, summary, status, role, link_id}`. |
| `GET /notes/{label}/documents`, `GET`/`PUT /notes/{label}/documents/{name}`, `POST /notes/{label}/notes` | Notizen und Specs einer Note: Namen, lesen mit `version`, ersetzen oder anlegen (`{content, version}`), datierten Eintrag anhängen (`{topic, discussed?, decided?, open?}`). |

  Projektübergreifend (Präfix `/notes`):

| Methode und Pfad | Zweck |
|---|---|
| `GET /notes/index` | Schlanker Index ohne Langtexte (siehe unten). |
| `GET /notes/due/count` | Nur der Zähler `{count, by_project}` für das Ausrufezeichen. |
| `GET /notes/due` | Alle fälligen Notes mit Grund, Topic-Pfad, eingetroffenen Auslösern und möglichen Aktionen. |
| `GET /notes/settings`, `PUT /notes/settings` | Die Optionen `max_topic_depth` und `review_days` lesen bzw. ändern. |
| `GET /api/v2/notices?project=&label=&side=note\|item&open=` | Die Hinweise einer Note (`side=note`, `label` ist das Note-Label) oder eines Items (`side=item`, `label` ist die Item-ID), älteste zuerst; mit `open=true` nur die unentschiedenen. |
| `POST /api/v2/notices/{id}/decision` | Einen offenen Hinweis entscheiden: `{decision, version?, promotion?}`; Antwort `{notice, note, item?}` (`note` ist bei Item-Hinweisen `null`, `item` nur bei `promote`). |
| `POST /notes/{project}/{label}/promote` | Eine Note zu Task, Story oder Epic befördern (siehe „Beförderung und Rückstufung“). |
| `POST /api/v2/items/{source_id}/{item_id}/demote` | Ein offenes Item zur Note zurückstufen (siehe „Beförderung und Rückstufung“). |

- Eingabe:
  - Zeitpunkte sind ISO-8601 **mit Zeitzone** (sonst 400 `bad_request`); die
    API gibt sie in UTC zurück. „Morgen früh“ löst der Aufrufer auf.
  - Notes tragen eine `version`; jede Änderung, `keep`, `finish`, `snooze`
    und `move` braucht die zuletzt gelesene (sonst 409 `version_conflict`).
    Topics, Auslöser und Links haben keine Version.
  - Geschlossene (archivierte) Notes und Notes im Papierkorb lassen sich nicht
    ändern, auch ihre Dokumente, Auslöser und Links nicht (409 `note_closed`
    bzw. `note_deleted`); lesen geht immer. Zurückholen: `restore`.
  - Auslöser: `time` braucht `at`; `event` braucht `target` (Label eines
    Items, im Projekt der Note oder in `target_project`) und `target_status`
    (`In progress`, `Awaiting confirmation`, `Completed`, `Rejected`) und legt
    einen Link mit Rolle `trigger` an; hat das Item den Status schon, feuert
    der Auslöser sofort (`already_met`). `topic_due` braucht ein Topic an der
    Note. Mit `trigger_mode` `any` genügt ein Auslöser, mit `all` müssen alle
    eingetroffen sein. Ein ungültiger Auslöser beim Zurückstellen ändert
    nichts.
  - Links: Das Ziel muss existieren (404 `link_target_not_found`, auch für
    Topics und Notes im Papierkorb); derselbe Link zweimal ist 409
    `link_exists`; der Link eines Ereignis-Auslösers geht nur mit dem
    Auslöser (409 `link_belongs_to_trigger`). Links auf Items speichern Projekt
    und Item-Label und folgen dem Item bei `retype`.
  - Projektübergreifend: Ein Item-Ziel (Link oder Ereignis-Auslöser) darf in
    einem anderen registrierten Projekt liegen; ein nicht registriertes
    Projekt ist 404 `link_project_unknown`. Links und Auslöser nennen das
    Ziel auch als `target_display` (`Projekt · Label`). Ein Statuswechsel
    feuert Auslöser in allen Projekten, auch einer, den ein Sync in die
    Primärquelle einspielt.
  - Erreichbarkeit: `GET /notes/{label}/links` (und die Antwort von `DELETE`)
    nennt je Link `reachable` und `unreachable_reason`
    (`project_not_registered` oder `source_unreadable`); die Auslöser in
    `NoteOut` haben beides ebenfalls (`reachable` ist `null` ohne Ziel). Der
    Wert wird beim Lesen einer Note, ihrer Links und der Fällig-Liste
    berechnet, nicht gespeichert; Index und Zähler prüfen nichts. Beim ersten
    Entdecken legt der Server einen Hinweis `project_unreachable` an (kein
    zweiter für dasselbe Ziel, auch nicht nach einer Entscheidung); er bleibt
    offen, wenn das Projekt zurückkehrt. Es entsteht kein Fehler.
  - Dokumente heißen `<LABEL>_notes.md`, `<LABEL>_spec.md` oder
    `<LABEL>_spec_<thema>.md` mit dem Label der eigenen Note, sonst 403
    `forbidden`.
  - Index: `GET /notes/index?project=&topic=&status=&due=&linked_item=&linked_project=&archived=`.
    Ohne Filter: die offenen Notes aller Projekte. `topic` braucht `project`
    und schließt Unter-Topics ein; `status` ist der abgeleitete Status
    (`waiting`, `due`, `snoozed`, `done`, `dropped`, `promoted`) und darf mehrfach
    stehen (`?status=waiting&status=due`): dann gilt jeder davon; `due=true` hält
    nur fällige; `linked_item` (in `linked_project`, sonst `project`) hält die
    Notes, die per Link oder Ereignis-Auslöser auf das Item zeigen;
    `archived=true` liest nur das Archiv; abgeschlossene Werte in `status` lesen das
    Archiv zusätzlich, offene und abgeschlossene dürfen gemischt werden.
  - Einstellungen: `PUT /notes/settings` mit `max_topic_depth` (1 bis 10) und/oder
    `review_days` (1 bis 3650), nur Ganzzahlen. Sie werden in `config.json`
    gespeichert und wirken sofort; schon tiefer verschachtelte Topics bleiben.
- Ausgabe:
  - Note: `{project, label, version, summary, body, status, stored_status,
    reason, topic, review_at, trigger_mode, triggers, archived, deleted,
    created, updated}`. `status` ist der abgeleitete Status (`due`, wenn ein
    Auslöser eingetroffen oder das Prüf-Datum verstrichen ist), `stored_status`
    der gespeicherte; `reason` ist `trigger`, `notice`, `topic_due` oder
    `review_expired` (in dieser Reihenfolge der erste zutreffende). `open_notices`
    listet die unentschiedenen Hinweise der Note.
  - Index: `{topics, notes}`; Notes nur mit `project`, `label`, `summary`,
    `status`, `reason`, `review_at`, `topic`, `archived`; Topics mit `path`
    (Namen von der Wurzel), `due_at`, `due` und `note_count`. Fällig-Liste: wie
    ein Index-Eintrag plus `topic_path`, `triggers` (die eingetroffenen) und
    `actions` (`keep`, `snooze`, `done`, `dropped`).
  - Dokumente: `{name, kind, content, version}`.
- Fehler: `{code, message, details}` wie oben. Zusätzlich:

| HTTP | Codes |
|---|---|
| 400 | `topic_too_deep` (Tiefe über `max_topic_depth`, auch beim Verschieben des ganzen Teilbaums), `topic_loop` (Topic unter sich selbst), `value_required`, `invalid_value` |
| 404 | `note_not_found`, `topic_not_found`, `trigger_not_found`, `link_not_found`, `link_target_not_found`, `link_project_unknown` (Projekt eines Link-Ziels nicht registriert), `source_gone` (unbekanntes Projekt) |
| 409 | `version_conflict`, `note_closed`, `note_deleted`, `note_not_restorable`, `note_same_project`, `topic_has_content` (`details.items`), `topic_deleted`, `topic_not_deleted`, `link_exists`, `link_belongs_to_trigger` |

### Hinweise zwischen Notes und Items

- Ein Hinweis sagt, dass sich die andere Seite eines Links geändert hat, und
  bleibt offen, bis jemand entscheidet. Felder: `{id, side, project, label,
  cause, counterpart, created_at, decided_at, decision, options}`; `project`
  und `label` nennen den Informierten, `counterpart` die Gegenseite.
- Hinweise an Notes (`side=note`) entstehen nur für Links mit Rolle `reference`,
  wenn das Item abgeschlossen (`item_completed`) oder verworfen
  (`item_rejected`) wird, in den Papierkorb kommt (`item_deleted`) oder seinen
  Typ wechselt (`item_retyped`, die Gegenseite trägt die neue ID). Bei
  `trigger`-Links entscheidet der Auslöser, `origin`-Links melden nie. Ein
  offener Hinweis macht die Note fällig (Grund `notice`); die Fällig-Liste
  nennt dafür die Aktionen `keep`, `detach`, `drop`, `promote`.
- Entscheidungen an Notes: `keep` (Link bleibt, Prüf-Datum neu), `detach`
  (der `reference`-Link zum Item wird entfernt), `drop` (Note verwerfen; meldet
  an die Items), `promote` (mit `promotion`, den Item-Feldern von `promote`
  unten: die Note wird befördert und danach der Hinweis entschieden; ohne
  `promotion` oder für eine nicht beförderte Note 409 `decision_not_available`).
- Hinweise an Items (`side=item`, Ursache `note_dropped` oder `note_promoted`)
  entstehen, wenn eine Note mit `reference`-Link auf das Item verworfen oder
  befördert wird; „erledigt“ meldet nichts. Einzige Entscheidung:
  `acknowledge`. Sie machen eine Note nie fällig.
- Fehler: 404 `notice_not_found`, 409 `notice_already_decided`, 409
  `decision_not_available`, 409 `version_conflict` (die Note hat sich seit
  `version` geändert), 400 `invalid_value` (Entscheidung der falschen Seite).
  Scheitert das Anlegen eines Hinweises, wird es protokolliert und die Änderung
  am Item oder an der Note bleibt gültig.

### Beförderung und Rückstufung

- `POST /api/v2/notes/{project}/{label}/promote`, Body `{version, item_type
  (Task|Story|Epic), title?, summary?, area, goal, completion_criteria,
  parent?, required_for_parent?, priority?, dependencies?}`, Antwort `{note,
  item}`. Das Item entsteht im Projekt der Note über den normalen Anlageweg, alle
  Backlog-Prüfungen gelten (z. B. 409 `parent_closed`, fehlende Pflichtfelder
  400). `title` und `summary` sind mit der Kurzfassung der Note vorbelegt. Der
  Langtext der Note wird der erste datierte Notizen-Eintrag „Aus Note … befördert“
  (eine Zeile je Aufzählungspunkt), die Notizen der Note hängen daran, Specs
  heißen danach `<ITEM>_spec[_thema].md`. Die Note ist `promoted`, archiviert und
  trägt einen Link mit Rolle `origin` auf das Item.
- Ein abgebrochener Aufruf lässt sich mit derselben `version` wiederholen: der
  `origin`-Link zeigt, dass das Item existiert, es laufen nur die fehlenden
  Schritte. Ist das Item inzwischen weg, antwortet die API 409
  `promote_origin_missing`. Scheitert genau das Setzen des Links direkt nach dem
  Anlegen, legt die Wiederholung ein zweites Item an.
- `POST /api/v2/items/{source_id}/{item_id}/demote`, Body `{version, topic?}`
  (Topic-Label im Projekt der Quelle), Antwort `{item, note}`. Zulässig nur bei
  Status Open, ohne Kinder (auch geschlossene zählen) und ohne dass ein anderes
  Item außerhalb des Papierkorbs das Item als Parent oder Dependency nennt.
  Die neue Note hat den Titel als Kurzfassung, die Zusammenfassung als Langtext,
  die Notizen und Specs des Items als Dokumente (`<NOTE>_notes.md`,
  `<NOTE>_spec[_thema].md`) und einen Link `origin` auf das Item. Das Item wird als
  Rejected mit der Resolution „zur Notiz zurückgestuft“ archiviert und löst keinen
  Hinweis für die neue Note aus. Wiederholung mit derselben Item-`version`
  verwendet die bereits angelegte Note weiter.
- Fehler (409): `demote_not_open`, `demote_has_children` und
  `demote_referenced` (jeweils mit `details.items`), `demote_document_name`
  (ein Dokument des Items lässt sich unter einem Note-Label nicht benennen;
  nichts wird geändert), `promote_origin_missing`; außerdem `version_conflict`,
  `note_closed`, `note_deleted`.

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

## Dateiformat: Notes-Ordner (Spiegel der Notes)

Die Notes eines Projekts laufen im selben Sync wie der Backlog (`POST /sources/{id}/sync`, siehe oben): die
Dateiseite ist der Ordner `notes/` im Markdown-Ordner des Projekts (`markdown_path`), die Datenbank hält die Wahrheit.
Er enthält nur diese Dateien, andere werden nicht gelesen. Ein Eintrag je Zeile, damit Git sauber zusammenführt.
Feldnamen sind englisch, Zeitpunkte UTC mit `Z` (Bruchteile von Sekunden nur, wo es welche gibt). Beschrieben in
`src_old/backend/todo_viewer/domain/notes_markdown.py`, gepinnt durch die Golden-Files in `src_old/backend/tests/golden/notes/`.

| Datei | Inhalt |
|---|---|
| `NOTE-001.md` | Eine Note: Kopf, Auslöser, Links, Langtext (siehe unten) |
| `NOTE-001_notes.md`, `NOTE-001_spec.md`, `NOTE-001_spec_<topic>.md` | Die Dokumente der Note, als Text unverändert |
| `new-<kurzname>.md` (+ `new-<kurzname>_notes.md` …) | Eine in den Dateien angelegte Note ohne Label (Claude in der Cloud); erste Zeile `# NEW` |
| `topics.md` | Alle Topics als eingerückte Liste |
| `counters.md` | Die höchste je vergebene Nummer je Typ |

```
# NOTE-001
Summary: <eine Zeile>
Status: waiting            # waiting, due, snoozed, done, dropped, promoted
Topic: TOPIC-001           # Label; leer = keins; new:<Name> = Topic ohne Label aus topics.md
Review: 2026-11-07T08:00:00Z
Mode: any                  # any oder all
Created: 2026-10-01T09:30:00Z
Updated: 2026-10-12T08:00:00Z
Archived: false
Deleted:                   # Zeitpunkt, wenn im Papierkorb
Triggers:
- time 2026-10-12T08:00:00Z [fired 2026-10-12T08:00:00Z]
- event Mein Projekt:STORY-003 Completed [fired 2026-10-12T08:00:00Z] [already_met]
- topic_due
Links:
- reference Mein Projekt:STORY-004
- reference topic:TOPIC-002
- reference note:NOTE-007
- origin Mein Projekt:STORY-009

<Langtext, Markdown, unverändert>
```

`Triggers:` und `Links:` fehlen, wenn es keine gibt; der Langtext folgt nach einer Leerzeile und endet die Datei,
wenn er leer ist. Links der Rolle `trigger` stehen nicht in `Links:`, sie ergeben sich aus den `event`-Auslösern.
`Created`/`Updated` dürfen bei einer Note ohne Label fehlen (der Import setzt den Zeitpunkt). Ein Projektname mit
`topic` oder `note` als ganzem Namen ist als Link-Ziel nicht von `topic:`/`note:` zu unterscheiden.
Zeilenenden (`\n` oder `\r\n`) bleiben, wie sie in der Datei sind.

`topics.md`: `- TOPIC-001 | <Name> | due=<Zeitpunkt> | created=<Zeitpunkt> | deleted=<Zeitpunkt>`, zwei Leerzeichen
Einrückung je Ebene (Kinder unter ihrem Parent); in Namen stehen `|` als `\|`, `\` als `\\` und Zeilenumbruch als
`\n`. Ein Topic ohne Label: `- NEW | <Name> | due=…`. `counters.md`: `NOTE: 15` und `TOPIC: 7`.

Verhalten im Sync (TASK-026): Topics, Notes und Note-Dokumente sind Einträge der Arten `topic`, `note`, `note_document`
im Stand je Eintrag, mit denselben Konflikten und Entscheidungen (`resolutions[].kind`). Eine Note im Papierkorb
oder Archiv bleibt eine Datei (`Deleted:`/`Archived:`). Eine endgültig gelöschte Note hat keine Datei; fehlt eine
Datei, die im Stand vorkommt, ist das ein Konflikt „im Ordner gelöscht“, gelöscht wird nur mit Entscheidung.
Labels vergibt nur die Datenbank: beim Import bekommt eine Note oder ein Topic ohne Label das nächste freie Label
des Projekts, Verweise darauf (`note:new-…`, `Topic: new:<Name>`) werden mit umgeschrieben, die Datei heißt danach
`NOTE-xxx.md` (sie wird im selben Lauf umbenannt, dazu muss der Ordner beschreibbar sein: bei `direction: from_md`
werden Einträge ohne Label nicht übernommen). Der Zähler der Datenbank ist danach mindestens das Maximum aus
Datenbank, `counters.md` und dem höchsten vorkommenden Label; `counters.md` wird mit den Notes geschrieben, ist aber
selbst kein Vergleichseintrag. Links auf unbekannte Projekte oder Labels bleiben erhalten. Topics tiefer als
`notes.max_topic_depth` werden eingelesen. Ein Formatfehler (unbekannte Kopfzeile, ungültiger Status oder Zeitpunkt,
Dateiname und Label verschieden) bricht den Sync vor jeder Änderung ab: 400 `sync_source_invalid`,
`details.reason` = `note_format`, die Meldung nennt Datei und Zeile. Ändert sich eine Datei zwischen Lesen und
Schreiben, antwortet der Sync mit 409 `mirror_conflict`; nichts wird überschrieben. Nicht gespiegelt:
Änderungshinweise, Projektliste, UI-Zustand, Notes-Einstellungen. Der Gesamtstand (`state`, Fingerabdrücke) und
`conflicts` umfassen die Notes; bestehende Stände von Projekten mit Notes gelten deshalb einmalig als geändert, bis
zum nächsten Sync. Vor einem Sync, der Notes in die Datenbank schreibt, entsteht ein Backup. Der Auto-Sync deckt
die Notes mit ab (dasselbe Verfahren).

## Dateiformat Version 2 (Neubau, Markdown-Spiegel)

Gilt für den Neubau (`EPIC-007`). Der alte Viewer liest und schreibt
weiter die Formate der beiden Abschnitte darüber. Grundsatz: so nah wie
möglich an Version 1 und am heutigen Notes-Format, damit der Harness wenig
ändern muss. Neu sind nur die `Uid`, die Platzhalter für neue Backlog-Einträge
und die Wecker; `counters.md` und Zeit-Auslöser an Notes entfallen.

### Ordner eines Projekts

| Pfad | Inhalt |
|---|---|
| `TODO.md` | aktive Items (nicht abgeschlossen, nicht im Papierkorb) |
| `archive.md` | Items mit `Completed`/`Rejected` und Items im Papierkorb |
| `items/<LABEL>/` | `<LABEL>_notes.md`, `<LABEL>_spec.md`, `<LABEL>_spec_<thema>.md`, Text unverändert |
| `notes/` | Notes, ihre Dokumente und `topics.md` wie heute, ohne `counters.md` |
| `alarms.md` | alle Wecker |

Andere Dateien werden nicht gelesen. Feldnamen und Werte sind englisch,
Inhalte in der Sprache des Projekts. Zeitpunkte sind UTC mit `Z`, Tage
`YYYY-MM-DD`. Zeilenenden bleiben, wie sie in der Datei sind.

### Verweise

Verweise (`Parent`, `Dependencies`, `Topic`, `Links`, `Target`) stehen in
den Dateien immer als **Label**, nie als `Uid`. Die `Uid` steht nur am
Eintrag selbst, dort ordnet der Sync ihn zu.

- In der DB hängen alle Verweise an der `uid`. Der Codec schreibt immer das
  aktuelle Label des Ziels; nach einem Typwechsel ziehen alle Verweise in
  den Dateien beim nächsten Schreiben nach.
- Labels werden nie wiederverwendet, und die DB merkt sich jedes Label, das
  ein Element je hatte. Ein Verweis auf ein altes Label (z. B. `STORY-012`
  nach dem Typwechsel zu `TASK-040`) findet deshalb weiter dasselbe Element;
  der Codec schreibt danach das aktuelle Label zurück.
- Ein Label, das es im Projekt nie gab, ist `unknown_reference`.

### Kennung

`TODO.md`, `archive.md` und `alarms.md` enthalten einen Absatz, der mit
`Format:` beginnt und `backlog format version 2` enthält, z. B.

```
Format: Claude_Harness backlog format version 2. The rules are defined in
`docs/techdocs/interfaces.md` of the ToDo Viewer.
```

Fehlt die Kennung oder nennt sie eine andere Version, bricht der Sync mit
`format_version` ab. Version 1 wird nicht gelesen; die Datenübernahme
(`STORY-082`) und der erste Sync nach dem Umstieg schreiben Version 2.

### Backlog-Einträge

Aufbau wie Version 1, eine Liste unter `## Work items`:

```markdown
- `STORY-012` **Kurzer Titel**
  - Uid: 3f0c2a9e-6b1d-4c57-9a8e-2d4b7c1e5f60.
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-004`, `STORY-010`.
  - Goal: Ergebnis. Folgezeilen sind
    vier Leerzeichen eingerückt.
  - Completion criteria: Wie das Ergebnis geprüft wird.
  - Summary: Kurzfassung für den Projektinhaber.
```

- **Felder und Reihenfolge** (fest; der Codec schreibt sie in dieser
  Reihenfolge, liest sie in jeder): `Uid`, `Type`, `Parent`,
  `Required for parent`, `Status`, `Created`, `Area`, `Priority`,
  `Dependencies`, `Goal`, `Completion criteria`, `Summary`, `Resolution`,
  `Deleted`. Andere Felder sind ein Fehler (`unknown_field`); `Notes` und
  `Spec` aus Version 1 entfallen, die Dokumente findet der Codec über
  `items/<LABEL>/`.
- **Pflicht:** `Uid` (außer bei neuen Einträgen), `Type`, `Status`, `Area`,
  `Priority`, `Dependencies`, `Goal`, `Completion criteria`; bei Story und
  Task `Parent`, bei vorhandenem Parent `Required for parent`; bei
  `Completed`/`Rejected` `Resolution`. `Created` darf bei neuen Einträgen
  fehlen (der Import setzt den Tag).
- **Werte:** `Type` `Epic`, `Story`, `Task`. `Status` `Open`,
  `In progress`, `Awaiting confirmation`, `Completed`, `Rejected`.
  `Priority` `Urgent`, `Important`, `Normal`, `Prospective`.
  `Required for parent` `Yes`, `No`. Verweise in Backticks, mehrere mit
  Komma, keiner als `None`.
- **Lage:** Welche Datei ein Eintrag hat und an welcher Stelle er steht, ist
  keine Information. Steht ein abgeschlossener Eintrag in `TODO.md`, liest
  der Codec ihn trotzdem und verschiebt ihn beim nächsten Schreiben nach
  `archive.md` (und umgekehrt). Neue Einträge hängt der Codec ans Ende.
- **Regeln** des Backlog-Formats (Parent-Lebenszyklus, keine Zyklen) gelten
  wie in der DB; ein Verstoß bricht den Sync ab (`rule_violation`, mit den
  blockierenden Einträgen).

### Neue Backlog-Einträge aus den Dateien

Eine LLM ohne API legt einen Eintrag **ohne `Uid`** an und gibt ihm einen
Platzhalter statt eines Labels:

```markdown
- `NEW-login-dialog` **Login-Dialog vereinfachen**
  - Type: Task.
  - Parent: `STORY-012`.
  - …
```

- Platzhalter: `NEW-` und ein Kurzname aus `a-z`, `0-9`, `-`, im Projekt
  eindeutig. Sonst `invalid_placeholder`.
- `Parent`, `Dependencies` und Verweise anderer Einträge dürfen
  Platzhalter nennen. Dokumente liegen in `items/NEW-<kurzname>/`
  (`NEW-<kurzname>_notes.md` …).
- Beim Sync vergibt die DB `Uid` und das nächste freie Label des Typs,
  ersetzt den Platzhalter in allen Verweisen, benennt Ordner und Dokumente um
  und schreibt den Eintrag mit beidem zurück. Bei einem Sync, der nur in die
  DB schreiben darf, werden neue Einträge nicht übernommen (wie heute bei
  Notes).
- Eine LLM erzeugt nie selbst eine `Uid` und nie ein Label.

### Notes und Topics

Wie im Abschnitt „Dateiformat: Notes-Ordner“ oben, mit diesen Änderungen:

- Im Kopf jeder Note steht nach der Überschrift `Uid: <uuid>`; eine neue
  Note (`new-<kurzname>.md`, erste Zeile `# NEW`) hat keine.
- `topics.md`: jede Zeile trägt `uid=<uuid>` nach dem Namen und
  `archived=<Zeitpunkt>`, wenn das Topic archiviert ist:
  `- TOPIC-001 | <Name> | uid=<uuid> | due=… | created=… | archived=… | deleted=…`.
  Ein neues Topic bleibt `- NEW | <Name> | …` ohne `uid`.
- `counters.md` entfällt; eine vorhandene Datei wird ignoriert und beim
  nächsten Schreiben gelöscht.
- Auslöser `time` entfallen (sie werden Wecker); eine `time`-Zeile ist ein
  Fehler (`unknown_trigger`). Es bleiben `event` und `topic_due`.

### Wecker

`alarms.md` mit einer Liste unter `## Alarms`:

```markdown
# Alarms

Format: Claude_Harness backlog format version 2.

## Alarms

- `ALARM-001` **Release vorbereiten**
  - Uid: 9b2e4f7a-1c3d-4e5f-8a6b-7c8d9e0f1a2b.
  - At: 2026-10-20T07:00:00Z.
  - Target: `STORY-012`.
  - Status: Pending.
  - Created: 2026-10-16.
```

- Felder in dieser Reihenfolge: `Uid`, `At`, `Target`, `Status`,
  `Snoozed until`, `Created`, `Deleted`. Der fett gesetzte Titel ist der
  Text des Weckers.
- `Target`: ein Label dieses Projekts, `<projekt>:<LABEL>` für ein anderes
  Projekt, oder `None`. Die Art des Ziels ergibt sich aus dem Präfix
  (`EPIC`, `STORY`, `TASK`, `NOTE`, `TOPIC`).
- `Status`: `Pending`, `Due`, `Snoozed` (dann `Snoozed until`), `Done`.
- Neue Wecker wie neue Backlog-Einträge: Platzhalter `NEW-<kurzname>`,
  ohne `Uid`.

### Fehler im Sync

Ein Formatfehler bricht den Sync vor jeder Änderung ab; die Meldung nennt
Datei und Zeile.

| Code | Bedeutung |
|---|---|
| `format_version` | Kennung fehlt oder ist nicht Version 2 |
| `unknown_field` | Feld, das das Format nicht kennt |
| `missing_field` | Pflichtfeld fehlt |
| `invalid_value` | unbekannter Typ, Status, Priorität oder Wecker-Status; ungültiger Tag, Zeitpunkt oder `Uid` |
| `duplicate_uid` | dieselbe `Uid` zweimal |
| `duplicate_label` | dasselbe Label oder derselbe Platzhalter zweimal |
| `unknown_reference` | `Parent`, `Dependencies`, `Topic` oder `Target` nennt ein Label, das es im selben Projekt nie gab (auch nicht als früheres Label); Verweise in andere Projekte bleiben ungeprüft erhalten |
| `invalid_placeholder` | Platzhalter mit ungültigem Namen |
| `file_label_mismatch` | Datei- oder Ordnername passt nicht zum Label |
| `unknown_trigger` | Auslöser-Art, die es nicht gibt (z. B. `time`) |
| `rule_violation` | Verstoß gegen die Regeln des Backlog-Formats |
| `merge_markers` | Datei mit Git-Merge-Markern |

### Beispiele

`tests/fixtures/mirror-v2/valid/` ist ein vollständiges Projekt mit allen
Feldern, neuen Einträgen mit Platzhaltern, Notes, Topics und Weckern.
`tests/fixtures/mirror-v2/invalid/<code>/` enthält je Fehlercode ein
Beispiel. Die Beispiele sind die Golden-Files der Codecs (`STORY-075`,
`STORY-079`, `STORY-080`).

## CLI: `todo.sh`

- Zweck: Steuerung des Docker-Containers.
- Aufruf / Endpunkt: `./todo.sh <start|stop|restart|down|update|logs|status|open>`.
- Eingabe: Befehlsname.
- Ausgabe: siehe [README](../../README.md#quickstart-docker).
- Fehler: unbekannter Befehl → Hilfetext, Exit-Code 1.
