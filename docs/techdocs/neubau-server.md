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
| auf beiden Seiten weg | – | Basis vergessen |

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
4. `auto(project)`: nur konfliktfreie Änderungen, löscht nie, sichert vorher die Datenbank, pausiert bei Problemen.
   Der Takt ist ein einzelner Termin `core.sync` im `Scheduler`, alle `auto_sync_interval_seconds` (Standard 30), nur
   solange mindestens ein Projekt Auto-Sync an hat (`refresh_auto()` setzt ihn neu).
5. Ereignis `core.sync.state` (öffentlich, also per SSE) `{project, state, reason}` nach jedem manuellen Lauf und bei jeder
   Zustandsänderung im Auto-Sync.

**Operationen des Core** (HTTP und MCP): `sync_status` (`GET /api/core/sync/{project}/status`), `sync_preview`
(`GET …/preview?direction=`), `sync_execute` (`POST …/execute`, Body `token`, `direction`, `decisions[{uid, choice}]`,
`delete_missing`). Fehlercodes: `sync_preview_stale` 409, `deletion_not_confirmed` 422, `mirror_not_configured` 404,
`mirror_blocked` 409, `mirror_conflict` 409, Formatfehler (Codes aus `docs/techdocs/interfaces.md`, Datei und Zeile in
`details`) 422. Bis `workspace` die Projekte liefert, ist `NoMirrorProjects` verdrahtet (kein Projekt hat einen Ordner).

## MCP

`/mcp` ist ein MCP-Server (Streamable HTTP, `mcp` 2.x) im selben Prozess. Jede Operation mit `mcp=True` ist ein Tool
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
- **Sync-Anbindung.** `workspace` liefert dem `SyncService` Ordner und Auto-Sync je Projekt (`MirrorProjects`); bei `workspace.project.changed` setzt die Composition Root den Auto-Sync-Termin neu.
- **Startordner des Browsers:** Einstellung `plugins.workspace.browse_start`, sonst Umgebung `BROWSE_START`, sonst der Home-Ordner.

## Konfiguration

`configs/viewer.json` (optional) und Umgebungsvariablen; die Umgebung gewinnt.

| Schlüssel (Datei) | Umgebung | Typ | Standard | Wirkung |
|---|---|---|---|---|
| `host` | `VIEWER_HOST` | String | `127.0.0.1` | Bind-Adresse (nur lokal laut Architektur) |
| `port` | `VIEWER_PORT` | Integer | `5412` | HTTP-Port des Neubaus |
| `log_dir` | `VIEWER_LOG_DIR` | Pfad | `logs` | Ordner mit `viewer.log` (JSON-Zeilen) |
| `db_path` | `VIEWER_DB` | Pfad | `configs/viewer.db` | SQLite-Datei des Neubaus |
| `backup_dir` | `VIEWER_BACKUP_DIR` | Pfad | `configs/backups` | Ordner der Datenbank-Sicherungen |
| `sse_keepalive_seconds` | – | Zahl | `15` | Abstand der Keep-alive-Zeilen |
| `auto_sync_interval_seconds` | `AUTO_SYNC_INTERVAL` | Zahl | `30` | Takt des Auto-Sync in Sekunden |
| `plugins.<id>` | – | Objekt | `{}` | Einstellungen eines Plugins (`context.settings`) |
| – | `VIEWER_CONFIG` | Pfad | `configs/viewer.json` | andere Konfigurationsdatei |

## Betrieb in der Entwicklung

```bash
PYTHONPATH=server/src .venv/bin/python -m viewer.app.main    # Port 5412
scripts/check-next.sh                                         # ruff, mypy, import-linter, pytest
```
