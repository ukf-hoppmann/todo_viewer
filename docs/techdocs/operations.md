# Betrieb

## Deployment

- Das `Dockerfile` baut in zwei Stages: zuerst das Frontend (`node:22-alpine`,
  `npm ci` + `npm run build`), dann das Backend-Image (`python:3.11-slim`), das
  API und `web/dist` ausliefert.
- `docker-compose.yml` startet den Dienst `todo-viewer` mit
  `restart: unless-stopped` auf Port 5411, nur an `127.0.0.1` gebunden (die API
  kann Items ändern und löschen), und bindet ein:
  - `./configs` → `/app/configs` (Quellen, UI-Zustand und die zentrale
    Datenbank `todo.db` bleiben auf dem Host),
  - `./logs` → `/app/logs` (Logdatei `todo-viewer.log`; bleibt beim Entfernen
    des Containers erhalten, per `.gitignore` nicht im Repo),
  - `/Users/hoppmann/Documents/GitHub` unter demselben Pfad, beschreibbar
    (Bearbeitungen landen in den Backlog-Dateien der Nachbar-Repos).
- Aufruf im Browser: `http://todo.localhost:5411`.
- Nach Code-Änderungen: `./todo.sh update` (Neubau ohne Cache).
- Zentrale Datenbank: SQLite-Datei `configs/todo.db` (bzw. `storage_url`) mit
  Projektliste, UI-Zustand und den Inhalten der Datenbank-Projekte, daneben im
  Betrieb `todo.db-wal` und `todo.db-shm`. Das Schema wird beim ersten Zugriff
  automatisch auf den aktuellen Stand migriert (Tabelle `schema_version`, nur
  vorwärts; Version 3 ergänzt die Spalte `mirror_database`, bestehende Projekte
  bekommen keinen Datenbank-Spiegel). Sicherung: bei gestopptem Container alle drei Dateien kopieren,
  im laufenden Betrieb `sqlite3 configs/todo.db ".backup configs/todo-backup.db"`.
- Speicherort eines Projekts wechseln (UI: ✎ → „In die Datenbank übernehmen…“
  bzw. „Als Markdown-Ordner ablegen…“; API: Sync, dann `PUT /sources/{id}` mit
  neuem `backend`): vorher die Datenbankdatei sichern (siehe oben). Der Wechsel
  löscht nichts. Die Markdown-Dateien bleiben nach dem Übernehmen liegen und
  werden zum Sync-Ordner; die Daten in der Datenbank bleiben nach dem Ablegen als
  Markdown liegen (sie werden nicht mehr gelesen, ein späteres Zurückstellen
  zeigt sie in der Vorschau als Unterschied). Beim Austragen eines
  Markdown-Projekts verschwindet seine Kopie in der Datenbank mit, ein
  Datenbank-Projekt mit Items lässt sich nicht austragen. Der Export in einen
  neuen Ordner schreibt die Kopfzeilen von `TODO.md`/`archive.md` in der
  gewählten Sprache (die UI schickt ihre eigene, die API standardmäßig `en`);
  Einträge und Dokumente sind inhaltlich gleich, Zeilenumbrüche und die
  Reihenfolge der Felder sind normalisiert. Ein bestehender Sync-Ordner behält
  seinen Kopftext.
- Erster Start nach dem Update von einer Version mit Projekten in
  `config.json`: Projekte und UI-Zustand werden in die Datenbank übernommen,
  alle `source_id`s ändern sich einmal (Agenten schlagen sie über den Pfad
  nach). Zurück zum alten Stand: älteres Image starten und `config.json.bak`
  sowie `ui_state.json.bak` zurückbenennen.
- Nach einem Update mit neuen Python-Abhängigkeiten (z. B. SQLAlchemy) lokal
  `.venv/bin/pip install -r backend/requirements-dev.txt`; das Image installiert
  sie beim Neubau selbst.
- Prüfungen laufen lokal über `scripts/check.sh` (ruff, mypy --strict,
  import-linter, pytest, tsc, eslint, vitest); es gibt keine CI.

## Laufender Betrieb

- Starten/Stoppen über `./todo.sh` (siehe [README](../../README.md)).
- Status: `./todo.sh status`; Live-Log: `./todo.sh logs` (folgt `logs/todo-viewer.log`).
- Erreichbarkeit: `GET /api/v2/health` antwortet mit `{"status": "ok", "api": "2"}`,
  ohne Backlog-Dateien zu lesen.
- Das Frontend wird pro Anfrage gesucht: ein späteres `npm --prefix web run build`
  wird ohne Neustart ausgeliefert.

## Log

Das Backend schreibt pro Ereignis eine Zeile (Format und Level: siehe
[Konfiguration](configuration.md), `LOG_FILE`/`LOG_LEVEL`):

```
<UTC-Zeit> <LEVEL> <event> logger=<modul> req=<id> key=value ...
```

Werte mit Leerzeichen, `=` oder `"` stehen in Anführungszeichen; verschachtelte
`details` werden zu `details.<schlüssel>=…`. Ein Stacktrace folgt eingerückt
(4 Leerzeichen) unter seiner Zeile.

| Event | Level | Wann | Felder |
|---|---|---|---|
| `startup` | INFO | Serverstart | `api`, `python`, `config_dir`, `frontend_dir`, `browse_start`, `log_file`, `log_level` |
| `request` | ERROR / WARNING / INFO / DEBUG | Jeder Request: 5xx (mit Stacktrace) / 4xx / schreibend / lesend sowie `PUT /ui-state` | `method`, `path`, `query`, `status`, `ms`; bei Fehlern `code`, `message`, `details.*`; beim Anlegen `source`, `type`, `item`; bei Quellen `target`, `source`; beim Sync `source`, `direction`, `confirm` |
| `file_written` | INFO (JSON-Konfiguration: DEBUG) | Datei geschrieben | `path`, `created` bei neuen Dateien |
| `backlog_unparsable` | WARNING | Backlog-Datei lässt sich nicht parsen (Projekt zeigt ⚠) | `source`, `path`, `error`; Stacktrace als `backlog_unparsable_trace` auf DEBUG |
| `ui_state_unreadable` | WARNING | `ui_state.json` einer früheren Version defekt oder nicht lesbar; übernommen wird ein leerer UI-Zustand | `path`, `error` |
| `sources_taken_over` | INFO | Projekte aus `config.json` in die Datenbank übernommen | `count`, `skipped` |
| `ui_state_taken_over` | INFO | `ui_state.json` in die Datenbank übernommen | – |
| `database_unavailable` | WARNING | Datenbank lässt sich nicht öffnen (Projekt zeigt ⚠ `db_unavailable`) | `source`, `error` |
| `folder_unreadable` | WARNING | Ordner-Browser kann einen Ordner nicht auflisten | `path`, `error` |

Alle Zeilen eines Requests tragen dieselbe `req`. Meldungen von uvicorn
erscheinen im selben Format mit `logger=uvicorn.error`.

Suchen, ohne die Datei ganz zu lesen:

```bash
grep -E ' (ERROR|WARNING) ' logs/todo-viewer.log | tail -20   # letzte Probleme
grep -A30 ' ERROR ' logs/todo-viewer.log | tail -60            # Fehler mit Stacktrace
grep 'code=version_conflict' logs/todo-viewer.log              # nach Fehlercode
grep 'STORY-016' logs/todo-viewer.log                          # nach Item-ID (Pfad oder item=)
grep ' req=1a2b3c4d ' logs/todo-viewer.log                     # alles zu einem Request
```

Ältere Einträge stehen in `todo-viewer.log.1` … `.5`.

## Fehlerbilder

| Symptom | Ursache | Behebung |
|---|---|---|
| Seite zeigt „Frontend not built“ (HTTP 503) | `web/dist/index.html` fehlt (lokaler Start ohne Build) | `npm --prefix web run build` |
| Projekt in der Liste ausgegraut mit ⚠ | Backlog-Ordner fehlt, ist kein Ordner, enthält keine `TODO.md` oder ist im Container nicht eingebunden | Pfad in der UI (✎) korrigieren; Ordner muss unter dem gemounteten Pfad liegen |
| Speichern bricht mit Hinweis auf externe Änderung ab (`version_conflict`/`file_changed`) | Der Eintrag wurde seit dem Lesen geändert bzw. die Datei während des Schreibens, z. B. durch einen Agenten | Nach dem nächsten Polling erneut bearbeiten |
| Projekt mit ⚠ „nicht im Backlog-Format“ (`unsupported_format`) | `TODO.md` ohne Format-Kennung, z. B. eine einfache Checkliste | Datei ins Backlog-Format überführen (Kennung und IDs) |
| Speichern schlägt mit `write_failed` fehl | Keine Schreibrechte auf den Backlog-Ordner | Rechte bzw. Volume-Mount (beschreibbar) prüfen |
| Ein Test meldet veraltete API-Typen | v2-API geändert, `openapi.json`/`schema.d.ts` nicht neu erzeugt | `.venv/bin/python backend/scripts/export_openapi.py && npm --prefix web run gen:api` |
| Sync bricht mit `sync_stale` ab | Seit der Vorschau hat sich die Datenbank oder der Ordner geändert (oder es fehlt das `token`) | Vorschau neu holen und bestätigen |
| Sync bricht mit `sync_source_invalid` ab (`details.reason`) | Der Sync-Ordner fehlt (`not_found`), hat keine `TODO.md` (`no_todo`) oder ist kein Backlog (`unsupported_format`, `parse_error`); es wurde nichts geändert | Ordner bzw. Datei reparieren, Vorschau wiederholen |
| Umstellen des Speicherorts mit `sync_required` abgelehnt | Beide Seiten sind nicht gleich (z. B. Fehlendes auf dem Ziel, das nicht gelöscht wurde) | Sync mit Vorschau ausführen (Fehlendes löschen), dann erneut umstellen |
| Datenbank-Projekt mit ⚠ `db_unavailable` | Die Datenbank lässt sich nicht öffnen (Datei gesperrt, `storage_url` falsch, Server nicht erreichbar); Log: `database_unavailable` | `storage_url` und Datei bzw. Dienst prüfen |
| Datenbank-Projekt lässt sich nicht austragen (`project_not_empty`) | Es hat noch Items | Zuerst auf Markdown ablegen (Umstellen) oder die Items löschen |
