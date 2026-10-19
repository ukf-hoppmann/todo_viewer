# Neubau: Server (`server/`)

Stand des Neubaus (`EPIC-007`); der alte Viewer in `src_old/` ist davon unberührt. Verbindliche Regeln:
[Architektur](../development/architecture.md) und Scope `server`. Entwurf:
`docs/todo/items/EPIC-007/EPIC-007_spec.md`.

## Aufbau

```
server/src/viewer/
  core/{domain,application,infrastructure,api}   Hülle ohne Fachlichkeit
  plugins/<id>/…                                 Fachlichkeit (noch leer)
  app/composition.py                             feste Plugin-Liste, Verdrahtung
  app/main.py                                    Start (uvicorn)
```

| Baustein | Schicht | Aufgabe |
|---|---|---|
| `DomainError`, `Event`, `Operation`, `HttpBinding`, `Settings`, `validate_plugins` | `domain` | reine Datentypen und die Prüfung der Plugin-Liste |
| `PluginDefinition`, `PluginContext`, `PluginHost`, Ports `Clock`, `EventBus`, `Scheduler` | `application` | Plugins laden, Dienste bauen, Operationen ausführen |
| `SystemClock`, `InProcessEventBus`, `AsyncioScheduler`, `load_settings`, `configure_logging` | `infrastructure` | Adapter der Ports, Konfiguration, Log |
| `create_http_app`, Routen aus Operationen, Fehler-Handler, `SseHub`, Request-ID | `api` | HTTP-Host, SSE |

Die Schichten sind mit import-linter geprüft (`server/pyproject.toml`).

## Plugins

Ein Plugin exportiert aus `plugin.py` eine `PluginDefinition` (`id`, `requires`, `operations`, `subscriptions`,
`build`). `build(context)` liefert das Dienste-Objekt; ein Operations-Handler hat die Form `handler(services, input)`
(sync oder async). Der Plugin-Host bricht den Start mit `PluginSetupError` ab bei: ID nicht kebab-case oder `core`,
doppelte ID, unbekanntes oder zyklisches `requires`, doppelter Operationsname, doppelte Route, doppeltes MCP-Tool,
gleiches Tabellen-Präfix.

## HTTP

- Eine Operation mit `HttpBinding(methode, pfad)` wird zu `<methode> /api/<id><pfad>`. `{name}` im Pfad füllt das Feld
  `name` des Inputs; bei `GET`/`DELETE` kommen die übrigen Felder aus der Query, bei `POST`/`PUT`/`PATCH` aus dem
  JSON-Body.
- Fehler: `{"code", "message", "details"}`. `not_found` 404, `version_conflict` und `mirror_conflict` 409,
  `invalid_input` und `validation_error` 422, `config_invalid` 500, unbekannte Codes 400, unerwartete Fehler
  `internal_error` 500. Im OpenAPI-Schema steht `ErrorBody` als Antwort `4XX`.
- `GET /api/core/health` → `{"status": "ok"}`. OpenAPI unter `/openapi.json`.
- Jede Antwort trägt `X-Request-ID` (vom Client übernommen, wenn sie `[A-Za-z0-9._-]{1,64}` ist).

## SSE

`GET /api/core/events` liefert `text/event-stream`. Nur Ereignisse mit `public=True` werden weitergegeben:

```
event: <topic>
data: <json>

```

Beim Verbinden kommen `retry: 3000` und `: connected`, danach alle `sse_keepalive_seconds` (Standard 15) `: keep-alive`.
Es gibt keine Zustellgarantie; der Client lädt nach einem Neuverbinden neu. Beim Herunterfahren schließt der Server alle
Verbindungen.

## Datenbank

SQLite über SQLAlchemy Core, Datei `configs/viewer.db`. Fremdschlüssel sind an; jede Transaktion beginnt mit einem
eigenen `BEGIN`, damit auch DDL zurückgerollt wird. Adapter holen die Verbindung mit
`with database.transaction() as tx: tx.connection`; Operationen mit blockierendem Handler laufen in einem Thread.

- **Migrationen** je Besitzer (`core` und jedes Plugin): `Migration(version, apply(connection))`, Versionen lückenlos ab 1.
  Beim Start (`create_app`) laufen die ausstehenden Migrationen in Abhängigkeitsreihenfolge (Core zuerst, dann nach
  `requires`), jede in einer eigenen Transaktion; der Stand steht in `core_migrations(owner, version)`. Ist die
  Datenbank neuer als der Code, bricht der Start mit `database_too_new` ab, eine fehlgeschlagene Migration mit
  `migration_failed` (nichts davon bleibt übrig).
- **Schemaprüfung** nach jeder Migration: Tabellen des Besitzers tragen das Präfix `<id>_` (Bindestriche als `_`),
  Fremdschlüssel zeigen nur auf eigene Tabellen, `core_*` und Tabellen der Plugins aus `requires`; sonst
  `schema_violation`. Präfixe zweier Plugins dürfen einander nicht überlappen (`a` und `a-b` gehen nicht zusammen).
- **Backups** (`BackupMaker`): vor der ersten ausstehenden Migration eines Starts nach
  `configs/backups/viewer-<UTC-Zeit>-<grund>.db`, nicht bei einer Datenbank ohne Tabellen; je Grund bleiben die
  letzten 10. Der Sync nutzt später den Grund `sync`.
- **Optimistische Sperre**: `update_with_revision(connection, table, where, expected_revision, values)` ändert die Zeile
  nur bei unveränderter `revision` und erhöht sie; sonst `version_conflict` oder `not_found`.
- **Core-Tabellen**: `core_migrations`, `core_ui_state(owner, document, updated_at)`,
  `core_sync_state(project_uid, uid, hash, synced_at)`.
- **UI-Zustand**: `GET/PUT /api/core/ui-state/{owner}` (Besitzer `[a-z][a-z0-9-]{0,63}`, Dokument ein JSON-Objekt bis
  256 KiB). `PUT` ersetzt das Dokument ohne Versions-Token; es gibt keine MCP-Tools dafür.
- **Browser-Logs**: `POST /api/core/client-log` (Operation `client_log`, kein MCP-Tool) nimmt einen Eintrag des Browser-Loggings
  an (`level` = `debug|info|warn|error`, `origin`, `id`, `time`, `session_id`, `route`, `element`, `action`, `message`,
  `user_message`, `error`, `data`) und schreibt ihn über structlog mit dem Logger `viewer.client` ins `viewer.log`
  (Felder `client_origin`, `client_id`, `session_id`, …). Begrenzung: Text höchstens 2000 Zeichen, `error` und `data` je
  16 KiB (größere werden durch `{truncated, size}` ersetzt), höchstens 100 Einträge je 60 Sekunden; darüber antwortet die
  Operation `{accepted: false}` und verwirft den Eintrag. Eine unbekannte Stufe ist ein `invalid_input`.

## Dateien (Spiegel-Ordner)

Der Port `FileStore` (`LocalFileStore` im Betrieb, `InMemoryFileStore` in Tests) liest und schreibt einen Ordner als
Menge von Textdateien und kennt keine Formate (die liefern die Codecs der Plugins). Pfade sind relativ und POSIX, ohne
`..` und nicht in `.git`.

- `read(folder, patterns)` → `FileSet` aus `FileEntry(path, text, version, newline)`. Muster relativ zum Ordner, `**`
  erlaubt. Der Text hat LF; `version` ist der SHA-256 der Bytes; `newline` ist das Zeilenende der Datei. Temporäre
  Dateien des Schreibens (`.<name>.<zufall>.tmp`) und `.git/` gehören nicht dazu.
- `write(folder, changes, expected, create_folder=False)`: Änderungen `WriteFile`, `RenameFile`, `DeleteFile`. Jeder
  berührte Pfad steht in `expected` (Version der Datei beim Lesen, `None` = darf nicht existieren). Weicht eine Version
  ab, folgt `mirror_conflict` mit den Pfaden in `details.paths`, bevor etwas geändert wurde. Geschrieben wird atomar
  (temporäre Datei, `fsync`, `os.replace`); bestehende Dateien behalten Zeilenende (CRLF/LF, die Mehrheit zählt) und
  Dateirechte, neue Dateien bekommen LF. Schlägt etwas mitten im Lauf fehl, werden alle berührten Dateien
  zurückgesetzt. Schreibende Zugriffe auf einen Ordner sind im Prozess serialisiert. Rückgabe: neue Versionen
  (`None` = gelöscht).
- `inspect(folder, patterns=("**/*.md",))` → `FolderState(status, files)` ohne Datenänderung. `status`:
  `ok`, `missing` (Ordner fehlt), `git_operation` (`.git/*.lock` im Repository oberhalb des Ordners, auch bei
  Worktree-`.git`-Dateien), `unreadable` (nicht UTF-8 oder nicht lesbar), `merge_markers` (Anfangs- und Endmarker
  `<<<<<<<`/`>>>>>>>` am Zeilenanfang). Liegt etwas anderes als `ok` vor, melden `read` und `write` `mirror_blocked`
  (HTTP 409) mit `details.state` und `details.files`, statt zu lesen bzw. zu schreiben.

## Sync (Datenbank ⇄ Markdown-Spiegel)

Der Sync-Dienst (`SyncService`) gleicht je Projekt die Datenbank (Wahrheit) mit dem Spiegel-Ordner ab. Er kennt weder
SQL noch Dateiformate noch Fachlichkeit. Jedes spiegelnde Plugin setzt in `PluginDefinition.mirror` eine Funktion
`services -> MirrorBinding(owner, codec, participant)`; der Dienst arbeitet mit allen Spiegeln eines Projekts zusammen.

**Ports eines Plugins**

- `MirrorCodec` (Dateien ⇄ Einträge): `patterns`, `decode(files)` (wirft `MirrorFormatError(code, message, file=…,
  line=…)`), `encode(upserts, removed, current)` → Änderungen an den Dateien. Ein Eintrag in `upserts` mit `placeholder`
  ersetzt den gleichnamigen neuen Eintrag in den Dateien.
- `SyncParticipant` (Datenbank ⇄ Einträge): `load(project)`, `resolve_labels(project, labels)` (auch frühere Labels →
  aktuelles Label), `assign_labels(project, entries, tx)` (Platzhalter → Label, in der Transaktion des Laufs),
  `apply(project, SyncChanges(created, updated, deleted), tx)`.
- `MirrorEntry(kind, label, fields, refs, uid, placeholder)`: `refs` hält alle Verweise (Feld → Labels), `fields` den
  Rest. Der Hash (SHA-256 über Art, Felder, Verweise) schließt das Label aus: Labels vergibt nur die Datenbank.
- `MirrorProjects` (liefert Ordner und Auto-Sync-Schalter je Projekt; erfüllt später `workspace`), `SyncStateStore`
  (`core_sync_state`).

**Vergleich** je `uid` mit dem Hash beim letzten Sync (Basis):

| Datenbank | Dateien | Ergebnis |
|---|---|---|
| gleich | gleich | nur Basis nachziehen |
| nur Dateien geändert | – | Dateien → Datenbank |
| nur Datenbank geändert | – | Datenbank → Dateien |
| beide geändert, oder beide neu mit verschiedenem Inhalt | – | Konflikt `both_changed` / `both_created` |
| neu auf einer Seite | fehlt | anlegen auf der anderen Seite |
| fehlt auf einer Seite, Basis vorhanden | – | Konflikt `deleted_in_files` / `deleted_in_database`, nie automatisch gelöscht |
| kurzlebiger Eintrag fehlt in der Datenbank, Dateien seit der Basis unverändert | = Dateien | in den Dateien löschen (kein Konflikt) |
| auf beiden Seiten weg | – | Basis vergessen |

Kurzlebig sind die Einträge einer Bindung mit `MirrorBinding(..., ephemeral=True)` (heute nur `alarms`); `compute_plan`
erhält ihre Arten als `ephemeral` und kennt sonst keine Fachlichkeit.

Verweise in Dateien werden vor dem Vergleich über `resolve_labels` auf das aktuelle Label abgebildet (Label-Historie).
Einträge aus den Dateien ohne `uid` (Platzhalter `NEW-<kurzname>`) sind neu; sie werden nur bei Richtung `both`
übernommen, weil der Rückschrieb von `uid` und Label dazugehört.

**Ablauf** (`status`, `preview`, `execute`, `auto`):

1. `status(project)` ändert nichts und liefert `in_sync`, `primary_changed` (Datenbank hat Neues), `mirror_changed`
   (Dateien haben Neues), `both_changed`, `conflicts` oder `paused` (Ordner fehlt/gesperrt/unlesbar, Merge-Marker,
   Formatfehler, kein Ordner konfiguriert) mit `reason` und betroffenen Dateien.
2. `preview(project, direction)` → `token`, `transfers`, `conflicts` (mit beiden Fassungen), `skipped`, `not_imported`.
   `direction`: `both`, `to_database`, `to_files`. Das Token ist zustandslos (SHA-256 über den Plan).
3. `execute(project, token, direction, decisions, delete_missing)`: weicht der Plan vom Token ab, `sync_preview_stale`.
   Je Konflikt eine Entscheidung `database`, `files` oder `defer`; eine Entscheidung, die löscht, braucht
   `delete_missing=true` (sonst `deletion_not_confirmed`). Reihenfolge: Backup der Datenbank (Grund `sync`) →
   eine Transaktion für alle Teilnehmer (uid vergeben, Labels vergeben, Platzhalter in allen Verweisen ersetzen, Änderungen
   anwenden) → Dateien schreiben (mit den beim Lesen erfassten Versionen, sonst `mirror_conflict`) → beide Seiten neu
   lesen und die Basis für alle beidseitig gleichen Einträge nachziehen. Schlägt das Schreiben der Dateien nach dem Commit
   fehl, bleibt die Datenbank richtig und der nächste Lauf holt auf.
4. `auto(project)`: nur konfliktfreie Änderungen, löscht nur kurzlebige Einträge (siehe oben), sichert vorher die Datenbank, pausiert bei Problemen.
   Der Takt ist ein einzelner Termin `core.sync` im `Scheduler`, alle `auto_sync_interval_seconds` (Standard 30), nur
   solange mindestens ein Projekt Auto-Sync an hat (`refresh_auto()` setzt ihn neu).
5. Ereignis `core.sync.state` (öffentlich, also per SSE) `{project, state, reason}` nach jedem manuellen Lauf und bei jeder
   Zustandsänderung im Auto-Sync.

**Operationen des Core** (HTTP und MCP): `sync_status` (`GET /api/core/sync/{project}/status`; neben `state`, den Zählern, `reason` und `files` auch `last_sync`, der Zeitpunkt des letzten Abgleichs aus `core_sync_state`), `sync_preview`
(`GET …/preview?direction=`), `sync_execute` (`POST …/execute`, Body `token`, `direction`, `decisions[{uid, choice}]`,
`delete_missing`). Fehlercodes: `sync_preview_stale` 409, `deletion_not_confirmed` 422, `mirror_not_configured` 404,
`mirror_blocked` 409, `mirror_conflict` 409, Formatfehler (Codes aus `docs/techdocs/interfaces.md`, Datei und Zeile in
`details`) 422. Die Projekte mit Ordner und Auto-Sync liefert das Plugin `workspace`.

## MCP

Die Zuordnung der Befehle der alten Helfer zu den Tools steht in `interfaces.md`, „MCP-Tools für den Harness“; der Core bietet `core_health`. `/mcp` ist ein MCP-Server (Streamable HTTP, `mcp` 2.x) im selben Prozess. Jede Operation mit `mcp=True` ist ein Tool
`<owner>_<name>` (Bindestriche der ID als `_`): Beschreibung aus `summary`, Eingabe-Schema aus der Input-Dataclass
(dasselbe `TypeAdapter`-Schema wie die HTTP-Route), `read_only_hint` für `kind="read"`, Ausgabe als JSON-Text. Fehler
sind Tool-Ergebnisse mit `isError` und dem JSON `{code, message, details}` — derselbe Inhalt wie die HTTP-Fehlerantwort;
ungültige Argumente haben `validation_error`, ein unbekanntes Tool `not_found`. Erlaubte Hosts: `127.0.0.1`,
`localhost`, `[::1]` und `todo.localhost` (Schutz vor DNS-Rebinding).

## Plugin `workspace` (Projekte und Element-Register)

`viewer/plugins/workspace/` (Schichten `domain`, `application`, `infrastructure`; ein Import-Linter-Vertrag hält die Richtung). Es ist das erste Fach-Plugin und das Fundament aller anderen: Projekte, die gemeinsame Identität der Elemente und der Ordner-Browser.

- **Tabellen** (Präfix `workspace_`): `projects` (`uid`, `name` eindeutig unter den nicht gelöschten, `mirror_folder`, `mirror_enabled`, `auto_sync`, `sync_direction`, `position`, `revision`, `deleted_at`), `element_kinds`, `elements` (`uid`, `project_uid`, `kind`, `label`, `revision`, `deleted_at`, `UNIQUE(project_uid, label)`), `label_counters`, `label_history`. Die Migration legt das Projekt „Allgemein“ an (ohne Ordner; weder umbenennbar noch entfernbar).
- **Elementtypen.** Ein Plugin meldet sie in `PluginDefinition.element_kinds` an (`ElementKind(kind, label_prefix)`) und trägt dafür `workspace` in `requires` ein (sonst lehnt `validate_plugins` ab). Die Composition Root schreibt die Typen aller aktiven Plugins nach dem Bau in `workspace_element_kinds`.
- **Register-Port** (`viewer.plugins.workspace.ElementRegistry`, über `context.required["workspace"].registry`): `register(tx, project_uid, kind)`, `relabel(tx, uid, new_kind)`, `get`, `find_by_label`, `bump_revision(tx, uid, expected)`, `mark_deleted`, `restore`, `purge`. Alle Methoden laufen in der Transaktion des Aufrufers, damit ein Plugin Element und eigene Zeilen atomar anlegt. Labels zählen je Projekt und Präfix vorwärts und werden nie wieder vergeben (auch nach Löschen, Entfernen und Typwechsel); jedes Label, das ein Element je hatte, bleibt in `label_history` und löst weiter auf (`find_by_label`, `GET …/labels/{label}`).
- **Operationen** (`/api/workspace/…`): `list_projects` (GET `/projects`), `create_project` (POST), `update_project` (PUT `/projects/{uid}`, mit `version`), `move_project` (POST `/projects/{uid}/move`), `remove_project` (DELETE, mit `version`; ein Projekt mit Inhalt braucht `confirm=true`, dann geht es samt Inhalt in den Papierkorb, ein leeres wird gelöscht), `browse_folders` (GET `/folders?path=`; Unterordner ohne versteckte, `has_mirror` bei `TODO.md`), `resolve_label`. Als MCP-Tools gibt es nur `list_projects`, `browse_folders` und `resolve_label`; was Einstellungen ändert, ist keins.
- **Ereignis** `workspace.project.changed` (öffentlich; `change`: `created`, `updated`, `moved`, `removed`).
- **Titel im Register.** `workspace_elements.title` (Migration v2) ist der Anzeigetitel; das Fach-Plugin gibt ihn bei `register(tx, project, kind, title)` mit und hält ihn mit `set_title(tx, uid, title)` aktuell. Suche (`ElementRegistry.search`, Operation `search_elements`) und Verknüpfungen nutzen ihn.
- **Verknüpfungen** (`workspace_links`: `uid`, `from_uid`, `to_uid`, `role` in `reference`/`origin`/`trigger`, `UNIQUE(from, to, role)`, beide Enden mit `ON DELETE CASCADE`). Sie hängen an den `uid`s und überleben so Typwechsel und Umbenennen; zu Elementen im Papierkorb bleiben sie und werden mit `deleted` markiert, ein endgültig gelöschtes Element nimmt seine Verknüpfungen mit. Port `Links` (`add`, `remove`, `outgoing`, `incoming`; in der Transaktion des Aufrufers, über `context.required["workspace"].links`; nach dem Commit meldet der Aufrufer mit `links.announce(change, link)`). Operationen `add_link` (POST `/links`), `remove_link` (DELETE `/links/{uid}`), `list_links` (GET `/elements/{uid}/links`), `search_elements` (GET `/elements?query=`), alle auch als MCP-Tool. Die Rolle `trigger` legt nur der Port an (für Auslöser der Notes); die Operationen lehnen sie ab (`trigger_link_reserved`). Eine Verknüpfung auf sich selbst (`invalid_link`) und eine doppelte (`link_exists`) werden abgewiesen. Ereignis `workspace.links.changed` (öffentlich; `change`: `added`, `removed`, dazu `uid`, `from_uid`, `to_uid`, `role`).
- **Sync-Anbindung.** `workspace` liefert dem `SyncService` Ordner und Auto-Sync je Projekt (`MirrorProjects`); bei `workspace.project.changed` setzt die Composition Root den Auto-Sync-Termin neu.
- **Papierkorb.** Ob ein Element im Papierkorb liegt, steht in `workspace_elements.deleted_at` (für alle Typen). Die besitzenden Plugins melden dem Dienst beim Bau je Elementtyp drei Ports an: `context.required["workspace"].trash.register(kind, children=…, restore_guard=…, purger=…)`. `children(tx, uid)` nennt die `uid`s aller direkten Kinder (gelöschte eingeschlossen), `restore_guard(tx, element)` wirft einen `DomainError`, wenn das Wiederherstellen gegen eine Regel des Plugins verstößt, `purger(tx, uid)` entfernt Plugin-Daten und Dokumente. Ein Typ ohne Anmeldung hat keine Kinder, keine Regel und keine eigenen Daten. Operationen: `delete_element` (DELETE `/elements/{uid}?version=&cascade=`; hat das Element aktive Nachkommen und fehlt `cascade`, ändert sich nichts und die Antwort nennt `has_children` und `children`; sonst gehen Element und Nachkommen mit demselben Löschzeitpunkt in den Papierkorb), `list_trash` (GET `/trash?projects=<uid,uid>&query=`, neueste zuerst), `restore_elements` und `purge_elements` (POST `/trash/restore`, `/trash/purge`, Body `{uids}`). Wiederherstellen holt die mit dem Element gelöschten Nachkommen mit (gleicher Löschzeitpunkt), prüft für jedes Element den `restore_guard` und weist ein Element eines entfernten Projekts ab (`project_in_trash`); endgültiges Löschen gilt nur für Elemente im Papierkorb (`not_deleted` sonst) und räumt Nachkommen zuerst ab; Verknüpfungen gehen über den Fremdschlüssel mit. Bei beiden Sammelaktionen übergeht der Server gewählte Nachkommen gewählter Elemente (Vorfahren-Regel) und führt alles in einer Transaktion aus. `purge_elements` ist kein MCP-Tool. Ereignis `workspace.element.changed` (öffentlich; `change`: `deleted`, `restored`, `purged`; `uids`).
- **Startordner des Browsers:** Einstellung `plugins.workspace.browse_start`, sonst Umgebung `BROWSE_START`, sonst der Home-Ordner.

## Plugin `backlog` (Epics, Stories, Tasks)

`viewer/plugins/backlog/` (Schichten `domain`, `application`, `infrastructure`), benötigt `workspace`. Es meldet die Elementtypen `epic`, `story`, `task` (Präfixe `EPIC`, `STORY`, `TASK`) im Register an; `uid`, Label und Revision gehören dem Register.

- **Tabellen** (Präfix `backlog_`): feste Nachschlagetabellen `backlog_types` (`Epic`, `Story`, `Task`), `backlog_statuses` (`Open`, `In progress`, `Awaiting confirmation`, `Completed`, `Rejected`, mit `final`) und `backlog_priorities` (`Urgent`, `Important`, `Normal`, `Prospective` mit Rang) – ein anderer Wert scheitert am Fremdschlüssel –, `backlog_areas` (`UNIQUE(project_uid, name)`), `backlog_items` (`uid` = `workspace_elements.uid`, `title`, `status`, `priority`, `area_uid`, `parent_uid`, `required_for_parent`, `goal`, `completion_criteria`, `summary`, `resolution`, `created`, `position`) und `backlog_dependencies`.
- **Fortschritt** (reine Funktion `item_progress`, Vorlage ist der alte Viewer): je Item erledigt/gesamt über alle Nachkommen, unabhängig von Filtern; optionale (`required_for_parent = false`) und abgelehnte Kinder zählen samt Unterbaum nicht; Parent-Kreise halten die Rechnung nicht auf.
- **Operationen** (`/api/backlog/…`, beide auch MCP-Tools): `list_items` (GET `/items?projects=&statuses=&priorities=&query=`, die Listen komma-getrennt; unbekannte Status oder Prioritäten → `invalid_input`) liefert die flache Liste mit Fortschritt, Version und den `uid`s der Abhängigkeiten (`dependencies`); `get_item` (GET `/items/{ref}?project=`) liefert alle Felder, Parent, Kinder (auch gelöschte, markiert) und Abhängigkeiten. `ref` ist eine `uid` oder ein Label (dann mit `project`; auch ein früheres Label löst auf).
- **Papierkorb.** Das Plugin meldet `children` (über `parent_uid`), `restore_guard` (kein Wiederherstellen unter einem Parent im Papierkorb: `parent_in_trash`) und `purger` (Zeilen und Abhängigkeiten) an.
- **Schreiben** (`EditService`, jede Operation eine Transaktion; Ereignisse nach dem Commit): `create_item` (POST `/items`: `project`, `type`, `fields`; Pflicht `title`, `area`, `goal`, `completion_criteria`; Status immer `Open`, das Label vergibt das Register), `update_item` (PUT `/items/{ref}`: `version`, `fields`, `resolution`; erlaubt sind `title`, `status`, `priority`, `required_for_parent`, `goal`, `completion_criteria`, `summary`, `area`, `parent`, `dependencies`), `move_item` (POST `/items/{ref}/move`: `version`, `parent`, `position` – ohne Parent wird das Item Wurzel und verliert `required_for_parent`, unter einem Parent wird es Pflichtkind, wenn es keinen Wert hat), `retype_item` (POST `/items/{ref}/retype`: `version`, `type` – das Register vergibt ein neues Label, die `uid` bleibt, Verweise auf das alte Label in den Texten der Items des Projekts folgen; die Antwort enthält `old_label`, `new_label` und den Hinweis `external_references_may_remain`), `reopen_ancestors` (POST `/items/{ref}/reopen`: das Item und seine geschlossenen Vorfahren von oben nach unten auf `In progress`) und `list_areas` (GET `/areas?project=`). Alle sind auch MCP-Tools. Die `version` ist die Revision des Registers (`version_conflict` bei Abweichung); `ref` ist `uid` oder Label (mit `project`). Texte werden getrimmt und zu einer Zeile zusammengefasst; `Completed` und `Rejected` verlangen eine `resolution` (`resolution_required`), ein anderer Status löscht sie. Ein Bereich entsteht mit dem ersten Item, das seinen Namen trägt.
- **Dokumente** (`backlog_documents`: `item_uid`, `name`, `kind` `notes`/`spec`, `content`, `revision`, `updated_at`; Migration v2; endgültiges Löschen des Items nimmt sie mit): Namen folgen dem Label – `<LABEL>_notes.md` (das erste Notiz-Dokument), `<LABEL>_spec.md`, `<LABEL>_spec_<thema>.md` (Thema aus Buchstaben, Ziffern, `-`); ein Typwechsel benennt sie um (Inhalt bleibt). Die Version eines Dokuments ist seine `revision`. Operationen (auch MCP): `list_documents` (GET `/items/{ref}/documents`), `get_document` (GET `…/documents/{name}`), `put_document` (PUT `…/documents/{name}`: `content`, `version`, `summary`; mit `version` wird ersetzt (`version_conflict`), ohne wird angelegt (`document_exists`)), `append_note` (POST `/items/{ref}/notes`: `topic`, `discussed`, `decided`, `open`, `summary`; hängt `## <Datum vom Server> — <Thema>` mit den nicht leeren Abschnitten `### Discussed/Decided/Open` an, der erste Eintrag legt das Dokument mit der Kopfzeile `# <LABEL> — <Titel>` an). Ein Item mit Notiz-Dokument braucht eine Kurzfassung (Regel `summary_required_with_notes`); sie wird mit dem ersten Notiz-Dokument in einer Transaktion gesetzt. `get_item` nennt die Namen (`notes`, `spec`). Ereignis `backlog.document.changed` (öffentlich: `uid`, `name`, `change`: `created`, `updated`).
- **Spiegel** (`infrastructure/mirror/`): `BacklogCodec` (Muster `TODO.md`, `archive.md`, `items/**/*.md`) und `BacklogParticipant`. Format: `docs/techdocs/interfaces.md`, „Dateiformat Version 2“; die Beispiele unter `tests/fixtures/mirror-v2/` sind die Golden-Files. Ein Item ist ein `MirrorEntry` mit `kind` `epic`/`story`/`task` (Felder `title`, `status`, `priority`, `area`, `created`, `goal`, `completion_criteria`, `summary`, `resolution`, `required_for_parent`, `deleted` als Tag; Verweise `parent` und `dependencies` als Labels, die Abhängigkeiten sortiert), ein Dokument ein Eintrag mit `kind` `backlog.document`, `label` = Dateiname, `uid` = `<Item-uid>/<notes|spec|spec_<thema>>` (die Endung statt des Namens, damit ein Typwechsel keine neue Identität ergibt) und dem Verweis `item`. Das Dokument eines neuen Items trägt den Platzhalter `<NEW-name>/<endung>`, `assign_labels` benennt es mit dem Item um. **Lesen:** Kennung (`format_version`), Felder und Werte (`unknown_field`, `missing_field`, `invalid_value`, auch Label-Präfix ≠ Typ), `duplicate_uid`, `duplicate_label`, `invalid_placeholder` (`NEW-` und `a-z0-9-`), `file_label_mismatch` (Dokument im Ordner eines anderen Labels), `rule_violation` (die Lebenszyklusregeln über die Einträge der Dateien; ein aktives Kind unter einem geschlossenen Parent wird an dessen `Parent`-Zeile gemeldet; `summary_required_with_notes` prüft der Spiegel nicht, ein Spiegel mit Notizen ohne Kurzfassung bleibt lesbar) – jeweils mit Datei und Zeile. `unknown_reference` kann nur die Datenbank entscheiden (frühere Labels): der Teilnehmer wirft ihn beim Schreiben mit der Zeile des Feldes (`MirrorEntry.source`, `source_lines`; sie gehören nicht zum Vergleich). **Schreiben:** nur was sich ändert: Felder werden einzeln ersetzt (Umbruch bei 76 Zeichen, Fortsetzung mit vier Leerzeichen, Verweise als Menge verglichen), neue Felder an ihrer Stelle in der Reihenfolge des Formats eingefügt, entfernte gelöscht; ein Eintrag wechselt nur die Datei, wenn sich seine Lage ändert (`Completed`/`Rejected` und Papierkorb → `archive.md`, sonst `TODO.md`); ein Platzhalter-Eintrag wird an seiner Stelle ersetzt (Label, `Uid`, `Created`), seine Dokumente und Ordner werden umbenannt; neue Einträge kommen ans Ende, `TODO.md` und `archive.md` entstehen aus einer Vorlage, eine leere Datei wird nicht angelegt, ein leerer Abschnitt trägt `No entries.`. **Teilnehmer:** `load` liefert alle Items (auch gelöschte) und Dokumente; `assign_labels` reserviert Labels im Register (`reserve_label`, `note_labels` für die Labels, die derselbe Lauf mit Uid aus den Dateien anlegt); `apply` legt Elemente mit der vergebenen `uid` und dem Label an (`register_as`), schreibt Felder, Verweise, Papierkorb-Zustand und Dokumente und prüft die Lebenszyklusregeln über das Projekt (`rule_violation`, eigene Mängel zurückkehrender Items zählen nicht neu); eine Löschung aus den Dateien (nur mit `delete_missing`) legt das Item in den Papierkorb, nicht endgültig.
- **Regeln** (`domain/lifecycle.py`, Vorlage der alte Viewer, auf `uid` umgestellt): `epic_without_required_child`, `required_children_not_done`, `children_still_active`, `parent_closed` (die Fehlerdetails nennen `ancestors` als `{uid, label}` von oben nach unten: so wird wieder geöffnet), `epic_with_parent`, `required_for_parent_missing`, `unknown_reference` (Parent und Abhängigkeiten müssen Items desselben Projekts sein), `parent_cycle`, `dependency_cycle`, `summary_required_with_notes`. Eine Änderung wird nur abgewiesen, wenn sie eine Verletzung einführt oder erweitert. Weitere Fehler: `not_editable`, `value_required`, `item_deleted`.
- **Ereignisse:** `backlog.item.changed` (öffentlich; `change`: `created`, `updated`, `moved`, `retyped`; `uid`) und `backlog.item.status_changed` (intern, für `notes`: `uid`, `label`, `project_uid`, `from`, `to`).

## Plugin `notes` (Notes und Topics)

`viewer/plugins/notes/` (Schichten `domain`, `application`, `infrastructure`), benötigt `workspace` und `backlog` (nur über den Port `BacklogGateway`, den `infrastructure/backlog_gateway.py` auf die Dienste von `backlog` abbildet; `backlog` kennt `notes` nicht). Es meldet die Elementtypen `note` (Präfix `NOTE`, Titel = Kurzfassung) und `topic` (Präfix `TOPIC`, Titel = Name) an. Der Spiegel (STORY-079) und die Wecker (STORY-080) folgen in eigenen Stories.

- **Tabellen** (Präfix `notes_`, Migration v1): `notes_statuses` (`waiting`, `due`, `snoozed`, `done`, `dropped`, `promoted`), `notes_topics` (`uid` = Register, `name`, `parent_uid`, `due_at`, `archived_at`, `system`), `notes_notes` (`uid` = Register, `summary`, `body`, `status`, `topic_uid`, `review_at`, `trigger_mode` `any`/`all`, `archived`), `notes_documents` (`note_uid`, `name`, `content`, `revision`, `updated_at`) und `notes_settings` (`key`, `value`). `system` markiert das neutrale Topic „Archiviert“ eines Projekts (nicht löschbar, nicht umbenennbar, nicht verschiebbar).
- **Status.** Gespeichert werden `waiting`, `snoozed`, `done`, `dropped`, `promoted`; `due` ist abgeleitet (reine Funktion `is_due`): eine Note in Gebrauch (nicht im Archiv, nicht im Papierkorb) mit `waiting`/`snoozed` ist fällig, sobald ihr `review_at` erreicht ist. `archived` heißt „im Archiv“: erledigte, verworfene und beförderte Notes immer, offene Notes, solange ihr Topic archiviert ist (sie lösen nichts aus). Das Prüfdatum einer neuen, behaltenen oder zurückgestellten Note und einer Note mit geändertem Text ist heute + `review_days` (Standard 30). Zeitpunkte ohne Zeitzone gelten als UTC.
- **Übergänge** (`domain/lifecycle.py`, rein): `keep` (nur das Prüfdatum rückt vor), `snooze` (`snoozed`, Datum gegeben oder Standard), `finish` (`done`/`dropped`/`promoted` → Archiv), `restore` (Archiv → `waiting` mit neuem Datum; nicht in ein archiviertes oder gelöschtes Topic: `topic_archived`). Alles außer `restore` verlangt eine Note in Gebrauch (`note_deleted`, `note_archived`).
- **Topics** (`domain/topics.py`, rein): Tiefe (Standard 3, Einstellung 1–10) für Anlegen **und** Verschieben des ganzen Teilbaums (`topic_too_deep`), `topic_loop`, `topic_other_project`, `topic_parent_missing`, `topic_archived`. Pläne für Löschen, Archivieren und Reaktivieren: ein Topic mit Inhalt (Unter-Topics oder Notes) braucht eine Wahl, sonst `topic_has_content` mit den Zahlen `active`, `archived`, `topics`. Wahl: archivierte Notes behalten (`keep_archived`: sie wandern ins Topic „Archiviert“, das beim ersten Bedarf angelegt wird), aktive Notes `move` (nach `move_to`, leer = ohne Topic), `delete` (mit dem Topic in den Papierkorb) oder beim Archivieren `archive` (mit dem Topic archiviert). `choice_missing` bei fehlender Wahl für vorhandene aktive Notes. Reaktivieren holt das Topic, archivierte Unter-Topics und genau die Notes zurück, die nur wegen des Topics archiviert waren (Status nicht abgeschlossen); unabhängig archivierte bleiben archiviert. Ein archivierter Parent muss zuerst zurück.
- **Operationen** (`/api/notes/…`, alle auch MCP-Tools außer den Einstellungen): `notes_index` (GET `/index?projects=&statuses=&query=`: alle Topics mit Zählern `open_notes`/`due_notes` – offene, nicht archivierte Notes samt Unter-Topics – und die Notes mit abgeleitetem Status), `get_note` (GET `/notes/{ref}?project=`: Langtext, Topic-Pfad, `status` abgeleitet und `stored_status`, Dokumente), `due_notes` (GET `/due`: Zahl und Liste), `create_note` (POST `/notes`: `project`, `fields` mit `summary`, `body`, `topic`, `review_at`, `trigger_mode`), `update_note` (PUT `/notes/{ref}`: `version`, `fields`; `null` leert `body`, `topic`, `review_at`; geänderter Text setzt ein neues Prüfdatum, wenn keines mitkommt), `keep_note`/`snooze_note`/`restore_note` (POST `/notes/{ref}/keep|snooze|restore`), `finish_note` (POST `…/finish`: `status` `done`/`dropped`; `promoted` setzt später das Befördern), `create_topic` (POST `/topics`), `update_topic` (PUT `/topics/{ref}`: `name`, `due_at`), `move_topic` (POST `…/move`), `topic_content` (GET `…/content`), `archive_topic`, `reactivate_topic`, `delete_topic` (POST `…/archive|reactivate|delete`; Wahl in `keep_archived`, `active_notes`, `move_to`), Dokumente `list_note_documents`, `get_note_document`, `put_note_document` und `append_note_entry` (wie `backlog`: Namen `<LABEL>_notes.md`, `<LABEL>_spec[_<thema>].md`, `revision` als Version, Schreiben nur bei einer Note in Gebrauch) und `get_notes_settings`/`update_notes_settings` (GET/PUT `/settings`, ohne MCP). Löschen, Wiederherstellen und endgültiges Löschen einer Note oder eines Topics ohne Wahl laufen über die Operationen von `workspace`. `ref` ist `uid` oder Label (mit `project`); `version` ist die Revision des Registers.
- **Auslöser, Hinweise, Befördern, Zurückstufen** (Migration v2: `notes_triggers`, `notes_notices`; `target_uid`, `subject_uid`, `source_uid` ohne Fremdschlüssel, weil sie auf Elemente verschiedener Plugins zeigen).
  - **Fällig-Entscheidung** `due_state(note, triggers, topic, open_notices, now)` (rein, `domain/due.py`): Grund in der Reihenfolge `trigger`, `notice`, `topic_due`, `review_expired`; `trigger_mode` `any`/`all`; ein gefeuerter Auslöser bleibt gefeuert, bis die Note zurückgestellt wird (`reset`); Notes im Archiv oder Papierkorb sind nie fällig. Zeit-Auslöser gibt es nicht (Wecker, STORY-080).
  - **Auslöser:** `event` (ein Item erreicht `In progress`, `Awaiting confirmation`, `Completed` oder `Rejected`; legt eine Verknüpfung der Rolle `trigger` Note → Item an, die sich mehrere Auslöser auf dasselbe Item teilen; hat das Item den Status schon, feuert er sofort, `already_met`) und `topic_date` (der Termin des Topics der Note; das Topic braucht einen Termin: `trigger_needs_topic_date`). Abonnement `backlog.item.status_changed` feuert die wartenden Auslöser auf das Item (nur Notes in Gebrauch). Operationen `add_trigger` (POST `/notes/{ref}/triggers`: `kind`, `target`, `status`), `remove_trigger` (DELETE `/triggers/{uid}`), `snooze_note` mit `trigger` ersetzt alle alten Auslöser, ohne `trigger` werden gefeuerte zurückgesetzt und ein vorbeigegangener Termin entfällt.
  - **Hinweise** (`notes_notices`: `side` `note`/`item`, `subject_uid` = wer informiert wird, `source_uid` das andere Ende, `kind`, `decided_at`, `decision`): an die Note, wenn ein Item mit `reference`-Verknüpfung `Completed`/`Rejected` wird (`item_completed`, `item_rejected`), in den Papierkorb kommt (`item_deleted`, aus `workspace.element.changed`) oder den Typ wechselt (`item_retyped`, aus `backlog.item.changed`); an das Item, wenn eine Note, die auf es verweist, verworfen oder befördert wird (`note_dropped`, `note_promoted`). Ein offener Hinweis gleicher Ursache und Gegenseite bleibt der einzige. Entscheidungen (`decide_notice`, POST `/notices/{uid}/decide`): an der Note `keep` (Prüfdatum rückt), `detach` (Verweis entfernen), `drop` (verwerfen), `promote` (befördern, mit `type` und `fields`); am Item `acknowledge`. Erst wirkt die Entscheidung, dann wird der Hinweis entschieden (ein Fehler lässt ihn offen). `list_item_notices` (GET `/items/{ref}/notices`). `get_note` nennt Auslöser (mit Ziel und `arrived`), offene Hinweise mit ihren Entscheidungen und den Grund; `due_notes` je Note Grund, Topic-Pfad, Auslöser, Hinweise und `due_since`: seit wann sie fällig ist, nach dem Grund (Auslöser: das späteste Eintreten, ein Topic-Termin-Auslöser mit dem Termin; Hinweis: der jüngste offene; Topic-Termin: der Termin; Prüfung: das Prüfdatum; reine Funktion `due_since` in `domain/due.py`).
  - **Befördern** (`promote_note`, POST `/notes/{ref}/promote`: `version`, `type`, `fields` mit `area`, `goal`, `completion_criteria`, optional `title`, `summary`, …): legt über das Gateway ein Item im Projekt der Note an (Titel und Kurzfassung aus der Kurzfassung der Note), verknüpft Note → Item mit `origin`, übernimmt Langtext und Notizen (Eintrag „Aus Note <LABEL> befördert“) und Specs (Namen auf das Label des Items) und schließt die Note als `promoted`. Wiederholbar: eine vorhandene `origin`-Verknüpfung verhindert ein zweites Item, der Marker ein zweites Übernehmen (`promote_origin_missing`, wenn das Item inzwischen fehlt). **Zurückstufen** (`demote_item`, POST `/items/{ref}/demote`: `version`, `topic`): nur `Open`, ohne Kinder, ohne Items, die von ihm abhängen (`demote_not_open`, `demote_has_children`, `demote_referenced`); legt die Note an (Kurzfassung = Titel, Langtext = Kurzfassung), verknüpft mit `origin`, übernimmt Notizen und Specs und setzt das Item auf `Rejected` („zur Notiz zurückgestuft“); eine abgebrochene Rückstufung wird fortgesetzt.
- **Spiegel** (`infrastructure/mirror/`, Format: `docs/techdocs/interfaces.md`, „Notes und Topics“; Golden-Files unter `tests/fixtures/mirror-v2/valid/notes/`): `NotesCodec` (Muster `notes/*.md`; `for_project(name)` bindet ihn an den Projektnamen, siehe Sync) und `NotesParticipant`. Eintragsarten `notes.topic` (`name`, `due_at`, `archived_at`, `deleted_at`, Verweis `parent`), `notes.note` (`summary`, `status`, `review_at`, `mode`, `archived`, `deleted_at`, `body`, `triggers`; Verweise `topic`, `reference`, `origin`, `trigger_targets`) und `notes.document` (wie im Backlog: `uid` = `<Note-uid>/<notes|spec|spec_<thema>>`, Platzhalter `<new-kurzname>/<endung>`). Zeitstempel `Created`/`Updated` gehören nicht zum Vergleich (`MirrorEntry.extra`). Verweise stehen in den Einträgen als blanke Labels oder Platzhalter (`new-idee`, `NEW-login-dialog`, `new:<Topicname>`), in den Dateien als `<Projektname>:<LABEL>`, `topic:<LABEL>`, `note:<LABEL>`; ein Ziel eines anderen Projekts bleibt `Name:LABEL` und wird über Projektname und Label aufgelöst. **Lesen:** `unknown_field`, `missing_field`, `invalid_value` (auch `Status: due`: abgeleitet, nie in einer Datei), `unknown_trigger` (alles außer `event` und `topic_due`, auch Zeit-Auslöser), `duplicate_uid`, `duplicate_label`, `file_label_mismatch`, `invalid_placeholder` – mit Datei und Zeile; `counters.md` wird ignoriert. **Schreiben:** eine Note ist eine ganze Datei aus dem Eintrag (Kopf, Auslöser, Links, Langtext), `topics.md` wird aus den vorhandenen Zeilen und den Änderungen neu aufgebaut (Reihenfolge bleibt, Kinder unter ihrem Parent, neue ans Ende); ein Platzhalter-Eintrag ersetzt seine Datei unter dem neuen Label, Dokumente werden umbenannt, `counters.md` wird beim nächsten Schreiben gelöscht. **Teilnehmer:** `load` (auch gelöschte; Auslöser und Verknüpfungen `reference`/`origin`), `resolve_labels` (Labels, frühere Labels, mit Projektname), `assign_labels` (`reserve_label`, `note_labels`), `apply` (`register_as`, Felder, Parent, Topic, Auslöser samt `trigger`-Verknüpfungen, Verknüpfungen, Papierkorb, Dokumente; ein unbekanntes Ziel ist `unknown_reference` mit Datei und Zeile, auch bei anderen Projekten; Auslöser werden aus der Datei übernommen, ohne das Item zu prüfen). Gelöscht wird aus den Dateien nie endgültig. Bekannte Grenze wie beim Backlog: ändert sich das Label eines Ziels (Typwechsel), zieht der Verweis in der Datei erst beim nächsten Schreiben der Note nach; ändern sich zugleich Datei und Datenbank der Note, ist es ein Konflikt.
- **Projektwechsel** (`move_note`, POST `/notes/{ref}/move`: `version`, `target_project`, `topic`; `RelocationService`): im Zielprojekt entsteht eine neue Note mit neuem Label (Texte, Status, Prüfdatum, Dokumente mit dem neuen Label im Namen, Verweise und Ereignis-Auslöser; ein Topic-Termin-Auslöser entfällt), die alte kommt in den Papierkorb; Fehler `same_project`, `topic_other_project`, `version_conflict`. Kompakter Index für Agenten: `index_lines` (GET `/index/lines`), Tool `notes_index_lines`; im `backlog` entsprechend `index_lines` (GET `/index`).
- **Papierkorb.** `children` eines Topics sind Unter-Topics und Notes (gelöschte eingeschlossen); `restore_guard`: eine Note oder ein Topic kommt nicht zurück, solange sein Topic im Papierkorb liegt (`topic_in_trash`); `purger` entfernt Zeilen (und Dokumente). `delete_topic` legt Topic, Unter-Topics und die nicht umgehängten Notes mit demselben Zeitpunkt in den Papierkorb, das Wiederherstellen des Topics bringt genau diese zurück.
- **Ereignisse** (öffentlich): `notes.note.changed`, `notes.topic.changed` (`uid`, `change`), `notes.document.changed`, `notes.settings.changed`; `delete_topic` meldet zusätzlich `workspace.element.changed` für die Papierkorbansicht.

Projektname und Zusatzangaben für Codecs: `MirrorConfig` trägt den Namen des Projekts (`name`); ein Codec mit `for_project(name)` wird damit gebunden (`bound_codec`), wenn er Verweise mit Projektnamen liest und schreibt (`notes`). `MirrorEntry.extra` führt Angaben mit, die der Codec braucht, die aber nicht zum Vergleich oder Hash gehören (Zeitstempel der Dateien).

### Zustand „offen“ im Register

`registry.register_state(kind, is_closed)` meldet je Elementtyp eine Prüfung des Besitzers an, `registry.is_open(tx, uid)` fragt sie ab: offen ist ein Element, das es gibt, das nicht im Papierkorb liegt und das sein Besitzer nicht geschlossen nennt; ohne Prüfung gilt es als offen. Backlog meldet Epic, Story und Task an (geschlossen bei `Completed` und `Rejected`), Notes die Note (erledigt, verworfen, befördert oder archiviert) und das Topic (archiviert). So fragen andere Plugins (z. B. `alarms`) nach, ohne den Besitzer zu kennen.

## Plugin `alarms` (Wecker)

`viewer/plugins/alarms/` (Schichten `domain`, `application`, `infrastructure`), benötigt nur `workspace`. Elementtyp `alarm` (Präfix `ALARM`, Titel = Text, ohne Text der Titel des ersten Elements). Keine Wiederholung. Ein Wecker ist eine Erinnerung, kein Planungselement: frei mit Text oder an Elemente gebunden; das Label dient nur als Schlüssel für Spiegel und Cloud ([STORY-089](../todo/items/STORY-089/STORY-089_notes.md)).

- **Tabellen** `alarms_alarms(uid, at, text, target_text, status, snoozed_until, done_at)` und `alarms_targets(alarm_uid, position, element_uid)` (Migration v2 übernimmt das frühere `target_uid` als erstes Element; schon erledigte Wecker bekommen `done_at` = Zeitpunkt der Migration). Die Elemente sind geordnet (das erste ist im Detail offen) und hängen nicht an den Verknüpfungen von `workspace`, damit „Verknüpfen“ am Element einen Wecker nicht still ändert. `target_text` hält Verweise in andere, hier unbekannte Projekte unverändert als Text (komma-getrennt).
- **Status** `Pending`, `Due`, `Snoozed`, `Done` (von Hand erledigt) und `Expired` (erloschen) (`domain/model.py`, rein). `due_now(alarms, now)`: `Pending` mit erreichtem `at` und `Snoozed` mit erreichtem `snoozed_until`, nie im Papierkorb. `next_due`: frühester Zeitpunkt der noch wartenden (auch ein vergangener). `snooze` (Standard eine Stunde, nur in die Zukunft), `finish(alarm, now)` setzt `done_at`, `undo` nimmt nur `Done` zurück (`Due`, wenn die Zeit vorbei ist, sonst `Pending`), eine Änderung von `at` setzt wieder `Pending`.
- **Den Elementen folgen.** `follow_targets(alarm, open_states, now)`: ist keins der Elemente mehr offen, wird ein wartender Wecker `Expired`; ist ein erloschener wieder an einem offenen Element, kehrt er zurück. Ohne Elemente erlischt nichts. Ob ein Element offen ist, sagt `registry.is_open` von `workspace` (siehe dort); der Wecker kennt weder Backlog noch Notes. `AlarmService.follow()` prüft alle Wecker mit Elementen nach jedem fremden Ereignis (Abonnement `*`, die eigenen `alarms.*` ausgenommen) und meldet `alarms.alarm.changed` (`reloaded`), wenn sich offen/Titel eines Elements geändert hat.
- **Aufräumen.** `to_purge`: `Done` und `Expired`, deren `done_at` `PURGE_AFTER` (24 h) zurückliegt, nicht im Papierkorb. `purge()` löscht sie endgültig (Zeile, Elemente, Register), ohne Papierkorb.
- **Auslösen.** `AlarmService.reschedule()` bestellt beim `Scheduler` genau einen Termin (Besitzer `alarms`) auf `next_wakeup`: den nächsten Wecker oder das nächste Aufräumen. Er läuft nach jeder Änderung, nach `workspace.element.changed` (Papierkorb), nach `core.sync.state` und wenn `follow()` etwas geändert hat. Beim Bau bestellt `start()` einen Lauf sofort (erst dann haben alle Plugins ihre Prüfung „offen“ angemeldet; der `AsyncioScheduler` hält ihn bis `start(loop)`). Ein Lauf: `follow()`, `fire()` (fällige auf `Due`, meldet `alarms.due` und `alarms.alarm.changed`), `purge()`, `reschedule()`. `Due` bleibt über einen Neustart.
- **Operationen** (`/api/alarms/…`, auch MCP): `list_alarms` (GET `/alarms?projects=&due_only=`), `get_alarm`, `create_alarm` (POST; `fields`: `at`, `targets` als Liste aus uid oder Label, `text` nur ohne Elemente Pflicht; `target` für ein Element geht weiter), `update_alarm` (PUT; `targets: []` löst alle), `snooze_alarm`, `finish_alarm`, `reopen_alarm` (POST `…/snooze|finish|reopen`; `version` ist die Revision des Registers). Die Antwort trägt `targets` (je `uid`, `label`, `title`, `kind`, `deleted`, `open`), `done_at` und `purge_at`. Löschen und Wiederherstellen über `workspace`.
- **Spiegel** (`infrastructure/mirror/`, Format: `interfaces.md`): `AlarmsCodec` und `AlarmsParticipant`; `alarms.md` wird ganz aus den Einträgen neu erzeugt, die Einleitung bleibt; `format_version` wird geprüft; Platzhalter `NEW-<kurzname>`; `Target` ist eine Liste aus `` `LABEL` `` oder `` `Projekt:LABEL` ``: ein unbekanntes Label im eigenen Projekt ist `unknown_reference`, ein unbekanntes anderes Projekt oder Label bleibt `target_text`. Ein in der Datei erledigter Wecker ohne `Done at` bekommt den Zeitpunkt des Syncs. Die Bindung ist kurzlebig (`ephemeral`): ein aufgeräumter Wecker verschwindet ohne Konflikt auch aus `alarms.md`. `Created` gehört nicht zum Vergleich.
- **Ereignisse:** `alarms.alarm.changed`, `alarms.due`.

## Datenübernahme aus dem alten Viewer

`python -m viewer.app.import_legacy [--legacy-db configs/todo.db] [--target configs/viewer.db] [--backup-dir configs/backups] [--log-dir logs] [--dry-run]` (Paket `viewer/app/import_legacy/`, Schicht `app`; liest die alte Datenbank mit einer eigenen Kopie der Tabellen `legacy_schema.py`, nie mit Code des alten Viewers). Er läuft im Projektordner (die Vorgaben sind Pfade von dort; das Paket `viewer` muss installiert sein, `pip install -e server`) und schreibt nur, wenn alles geprüft ist.

- **Ablauf.** (1) Alte Datenbank schreibgeschützt lesen (`LegacyError`, wenn Datei oder Tabellen fehlen). (2) Alles prüfen (`validate.py`): ein Markdown-primäres Projekt (`backend = markdown`) bricht ab und wird genannt (erst im alten Viewer in seine Datenbank spiegeln, `STORY-060` Frage 1 und 35); unbekannte Priorität, Status, Typ, Modus, Auslöser-Art, Rolle, ein Label ohne `PRÄFIX-Nummer`, doppelte Labels oder Projektnamen brechen mit der **ganzen** Liste ab. (3) Das Ziel muss leer sein (nur das eingebaute Projekt, keine Elemente), sonst Abbruch. (4) Besteht die Zieldatei schon, kommt ein Backup (`<backup-dir>/viewer-<Zeit>-import.db`). (5) Die Anwendung wird gebaut (Migrationen, Elementtypen) und alles in **einer** Transaktion geschrieben. (6) Bericht auf stdout und in `<log-dir>/import-<Zeit>.log`. `--dry-run` macht alles in einer Wegwerf-Datenbank und lässt Ziel, Backups und Logs unberührt.
- **Abbildung.** Projekte: `id` → `uid`; Spiegel-Ordner = `sync_path`, eingeschaltet, wenn vorhanden und nicht `mirror_disabled`; `auto_sync` übernommen, Richtung `both`; ein Projekt „Allgemein“ wird das eingebaute; Reihenfolge nach der alten `position`. Elemente (Items, Topics, Notes): `uid` und Label bleiben; `deleted` → `deleted_at`; Label-Verlauf und Zähler (höchstes Label je Präfix, dazu `note_counters`). Priorität (ohne Rücksicht auf Groß-/Kleinschreibung): `Urgent`/`Important`/`Normal`/`Prospective` unverändert, `High` → `Urgent`, `Medium` → `Important`, `Low` → `Normal`, `dringend`/`wichtig`/`perspektivisch` wie im alten Viewer, leer → `Normal`. Bereiche → `backlog_areas` je Projekt. `location` entfällt (das Archiv ist der Endstatus). Zusatzfelder → ein Eintrag „Übernommene Zusatzfelder“ (Datum des Imports) in `<LABEL>_notes.md` (`STORY-060` Frage 4). Links → `workspace_links` über Projekt und Label des Ziels. Zeit-Auslöser an Notes → Wecker mit der Note als Ziel (`fired_at` gesetzt → `Due`, sonst `Pending`; `STORY-060` Frage 7); Ereignis-Auslöser behalten Status, Zustand und ihre Verknüpfung `trigger`; `topic_due` → `topic_date`. Hinweise → `notes_notices` (`project_unreachable` entfällt). Nicht übernommen: `ui_state`, `sync_entries` (der neue Sync fängt ohne Stand an).
- **Wiederholbar.** Erzeugte `uid`s (Bereiche, Verknüpfungen, Auslöser, Wecker, Hinweise) sind `uuid5` aus stabilen alten Schlüsseln: zwei Läufe auf frische Datenbanken ergeben dieselben Zeilen (bis auf das eingebaute Projekt, das die Migration anlegt).
- **Bericht.** Zahlen je Typ (Projekte, Items je Typ, Notes, Topics, Dokumente, Verknüpfungen, Auslöser, Wecker, Hinweise, Bereiche) und eine Zeile je Abweichung: leere Priorität oder alter Wert, fehlender Parent/Topic/Ziel, Abhängigkeit oder Verknüpfung ohne Ziel, doppelte Verknüpfung, Dokument ohne Item oder ohne Namensliste, Hinweis „Projekt nicht erreichbar“, unbekannter Zähler.
- **Tests.** Synthetische alte Datenbank aus `tests/helpers/server/legacy_db.py` (Fälle: `tests/fixtures/legacy-db/README.md`); dort liegt nie eine echte Datenbank. Ein Test prüft, dass die Kopie des Schemas zu `src_old/…/schema.py` passt (Quelltext, kein Import).

## Sync: Anzeige-Unterschiede und Dateiordner

Ergänzungen aus dem Spiegel des Backlogs: Weicht in einem Eintrag nur das Label ab (Typwechsel in der Datenbank, in der Datei steht noch das alte), ist das kein Konflikt: `compute_plan` lässt die Datei nachziehen (`files`/`update`); Verweise in anderen Einträgen ziehen beim nächsten Schreiben nach (sie lösen über die Label-Historie weiter auf). Ein Typwechsel ändert den Hash jedes Referrers (Labels gehören zu den Verweisen); wird derselbe Eintrag gleichzeitig in der Datei geändert, ist das ein Konflikt, den der Besitzer entscheidet. Die `uid` neuer Einträge darf der Teilnehmer selbst bilden (Dokumente): `_write_files` findet den Eintrag dann über sein Label. `assign_labels` bekommt zusätzlich `taken`, die Labels, die derselbe Lauf mit `uid` aus den Dateien anlegt. Der Datei-Port entfernt Unterordner, die durch Löschen oder Umbenennen leer werden (nie den Spiegel-Ordner). **Muster für den Datei-Port:** `Path.glob` (Python 3.11) lässt `**` am Ende nur Ordner treffen; Muster für Dateien in Unterordnern heißen deshalb `items/**/*.md`.

## Konfiguration

`configs/viewer.json` (optional) und Umgebungsvariablen; die Umgebung gewinnt.

| Schlüssel (Datei) | Umgebung | Typ | Standard | Wirkung |
|---|---|---|---|---|
| `host` | `VIEWER_HOST` | String | `127.0.0.1` | Bind-Adresse (nur lokal laut Architektur) |
| `port` | `VIEWER_PORT` | Integer | `5411` | HTTP-Port des Neubaus |
| `log_dir` | `VIEWER_LOG_DIR` | Pfad | `logs` | Ordner mit `viewer.log` (JSON-Zeilen) |
| `db_path` | `VIEWER_DB` | Pfad | `configs/viewer.db` | SQLite-Datei des Neubaus |
| `backup_dir` | `VIEWER_BACKUP_DIR` | Pfad | `configs/backups` | Ordner der Datenbank-Sicherungen |
| `static_dir` | `VIEWER_STATIC_DIR` | Pfad | `client/dist` | gebautes Frontend, das der Server unter `/` ausliefert (`core/api/frontend.py`); fehlt der Ordner, gibt es nur die API |
| `sse_keepalive_seconds` | – | Zahl | `15` | Abstand der Keep-alive-Zeilen |
| `auto_sync_interval_seconds` | `AUTO_SYNC_INTERVAL` | Zahl | `30` | Takt des Auto-Sync in Sekunden |
| `plugins.<id>` | – | Objekt | `{}` | Einstellungen eines Plugins (`context.settings`) |
| – | `VIEWER_CONFIG` | Pfad | `configs/viewer.json` | andere Konfigurationsdatei |

## Betrieb in der Entwicklung

```bash
PYTHONPATH=server/src .venv/bin/python -m viewer.app.main    # Port 5411
scripts/check-next.sh                                         # ruff, mypy, import-linter, pytest
```
