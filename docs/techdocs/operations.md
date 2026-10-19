# Betrieb

## Deployment

- Das `Dockerfile` baut in zwei Stages: zuerst das Frontend (`node:22-alpine`,
  `npm ci` + `npm run build`), dann das Backend-Image (`python:3.11-slim`), das
  API und `src_old/web/dist` ausliefert.
- `docker-compose.yml` startet den Dienst `todo-viewer` mit
  `restart: unless-stopped` auf Host-Port 5412, nur an `127.0.0.1` gebunden (die API
  kann Items ändern und löschen), und bindet ein:
  - `./configs` → `/app/configs` (Quellen, UI-Zustand und die zentrale
    Datenbank `todo.db` bleiben auf dem Host),
  - `./logs` → `/app/logs` (Logdatei `todo-viewer.log`; bleibt beim Entfernen
    des Containers erhalten, per `.gitignore` nicht im Repo),
  - `/Users/hoppmann/Documents/GitHub` unter demselben Pfad, beschreibbar
    (Bearbeitungen landen in den Backlog-Dateien der Nachbar-Repos).
- Aufruf im Browser: `http://todo.localhost:5412`.
- Nach Code-Änderungen: `./todo.sh update` (Neubau ohne Cache).
- Zentrale Datenbank: SQLite-Datei `configs/todo.db` (bzw. `storage_url`) mit
  Projektliste, UI-Zustand und den Inhalten der Datenbank-Projekte, daneben im
  Betrieb `todo.db-wal` und `todo.db-shm`. Das Schema wird beim ersten Zugriff
  automatisch auf den aktuellen Stand migriert (Tabelle `schema_version`, nur
  vorwärts; Version 3 ergänzt die Spalte `mirror_database`, bestehende Projekte
  bekommen keinen Datenbank-Spiegel; Version 5 die Spalte `mirror_disabled`, bestehende
  Datenbank-Projekte mit Ordner behalten ihren Spiegel eingeschaltet; Version 6 legt die Tabellen für
  Topics, Notes, Links, Auslöser, Note-Dokumente und die Label-Zähler an; Version 7 die Tabelle `note_notices` für die Hinweise zwischen Notes und Items; Version 8 die Tabelle `sync_entries` mit der Version jedes Items und Dokuments auf beiden Seiten nach dem letzten Sync, je Projekt und Markdown-Ordner, nur Versionen). Vor einer Migration legt der Dienst ein Backup an (siehe unten). Sicherung: bei gestopptem Container alle drei Dateien kopieren,
  im laufenden Betrieb `sqlite3 configs/todo.db ".backup configs/todo-backup.db"`.
- Primärquelle eines Projekts wechseln (UI: ⚙ → Projekte → „Einrichtung“ →
  „Zu Markdown wechseln…“ bzw. „Zur Datenbank wechseln…“; API: Sync, dann `PUT /sources/{id}` mit neuem `backend`): Der
  Dienst sichert die bisherige Primärquelle selbst (nächster Punkt); die
  Datenbankdatei zusätzlich zu sichern (siehe oben) schadet nicht. Der Wechsel
  löscht nichts. Die bisherige Seite bleibt als Spiegel: nach „Markdown →
  Datenbank“ bleibt der Ordner als Spiegel liegen (`sync_path`), nach
  „Datenbank → Markdown“ bleibt die Kopie in der Datenbank (Datenbank-Spiegel
  eingeschaltet). Den Spiegel abschalten: bei einem Datenbank-Spiegel löscht das
  die Kopie in der Datenbank, bei einem Markdown-Spiegel schaltet es nur den Spiegel ab: der Ordner bleibt
  gespeichert, „Markdown-Spiegel einschalten“ braucht keinen neuen (den Ordner selbst löscht
  „Ordner ändern…“ mit leerem Pfad; ⚙ → Projekte). Beim Austragen eines Markdown-Projekts verschwindet
  seine Kopie in der Datenbank mit, ein Datenbank-Projekt mit Items lässt sich
  nicht austragen. Der Export in einen neuen Ordner schreibt die Kopfzeilen von
  `TODO.md`/`archive.md` in der gewählten Sprache (die UI schickt ihre eigene, die
  API standardmäßig `en`); Einträge und Dokumente sind inhaltlich gleich,
  Zeilenumbrüche und die Reihenfolge der Felder sind normalisiert. Ein
  bestehender Spiegel-Ordner behält seinen Kopftext.
- Auto-Sync (pro Projekt in Einstellungen → Projekte → Einrichtung, beim Spiegel
  „Ein, Sync automatisch“; Standard: „Ein, Sync von Hand“): alle
  `AUTO_SYNC_INTERVAL` Sekunden (Standard 30) prüft der Viewer jedes Projekt mit
  Schalter und Spiegel und überträgt Konfliktfreies in beide Richtungen; Konflikte
  und Löschungen bleiben offen (Zahl in der Projektkarte und als ⚠ in der Sidebar) bis
  zur Entscheidung im Sync-Dialog. Eine Änderung wird erst übernommen, wenn sie bei zwei
  Prüfungen gleich war. Der Lauf pausiert (Karte: „Auto-Sync pausiert“, Log
  `auto_sync_paused`), wenn der Ordner fehlt oder nicht lesbar ist oder
  Git-Merge-Marker enthält; die nächste gute Prüfung setzt fort. Das Log nennt
  jeden Lauf (`auto_sync_run`). Backups: Grund `auto`, höchstens eines pro Stunde;
  aufbewahrt werden die letzten 10 und je Tag der letzten 14 Tage das jüngste.
  Ohne eingeschalteten Schalter läuft kein Timer.
- Notes im Sync: Ist ein Projekt mit Spiegel-Ordner angelegt, liegen die Notes im Unterordner `notes/` des
  Markdown-Ordners (Format: [Schnittstellen](interfaces.md)); `git add`/`pull` dieses Ordners trägt Notes zwischen
  Rechnern und in die Cloud (claude.ai). Eine dort angelegte Note heißt `new-<kurzname>.md` und bekommt beim
  nächsten Sync ihr Label (die Datei heißt dann `NOTE-xxx.md`). Konflikte entscheidest du im Sync-Dialog.
  Meldet der Sync `note_format`, nennt die Meldung Datei und Zeile; er hat nichts geändert. Beim ersten Sync
  nach dem Update gilt der Gesamtstand von Projekten mit Notes einmalig als geändert.
- Stand je Eintrag: Nach jedem Sync speichert die Datenbank die Version aller Items
  und Dokumente, die dann auf beiden Seiten gleich sind (`sync_entries`, Schlüssel
  Projekt, Markdown-Ordner, Art, Label, Name). Daran erkennt der nächste Sync, welche
  Seite einen Eintrag geändert hat. Aufgeschobene Konflikte bekommen keinen neuen
  Stand. Ändert man den Ordner des Projekts, beginnt es für den neuen Ordner ohne
  Stand (nur auf einer Seite vorhanden = neu, auf beiden verschieden =
  Konflikt); der Stand des alten Ordners bleibt liegen und gilt wieder, wenn man
  zu ihm zurückkehrt. Kein Inhalt wird gespeichert.
- Sync-Status: Nach jedem Sync über die API speichert die Datenbank einen
  Fingerabdruck beider Seiten und die Zeit (Spalten `last_sync_at`,
  `synced_primary`, `synced_mirror`); der Status (`GET /sources/{id}/sync-status`)
  liest erst beim Aufruf beide Seiten eines Projekts mit Spiegel (gemessen
  13 ms bei 42 Items) und läuft nicht im Takt der UI-Abfrage. `unknown`
  verschwindet mit dem ersten Sync (oder sobald beide Seiten gleich sind);
  `unreadable` heißt: der Markdown-Ordner fehlt teilweise oder ist kein
  Backlog, ein Sync liest ihn dann nicht.
- Backup beim Wechsel der Primärquelle: Vor jedem Wechsel (`PUT /sources/{id}`
  mit neuem `backend`, nachdem Sync und Prüfungen bestanden sind) legt der Dienst
  unter `<CONFIG_DIR>/backups/<Projekt>_<id8>/<JJJJMMTT-HHMMSS>/` einen
  Backlog-Ordner ab (`TODO.md`, `archive.md`, `items/…`). Bei einem
  Markdown-Projekt ist er eine Byte-Kopie der Dateien (nur diese, jede Kopie
  wird gegen das Original geprüft), bei einem Datenbank-Projekt ein
  Markdown-Export mit Papierkorb, Archiv, Notes und Specs, danach gegen die
  Datenbank geprüft. Schlägt das fehl (z. B. kein Schreibrecht, Platte voll),
  antwortet der Wechsel mit 409 `backup_failed` (`details.reason`), nichts
  wird umgestellt und ein angefangener Backup-Ordner wird entfernt.
  Wiederherstellen: den Backup-Ordner als Markdown-Projekt eintragen
  (`POST /sources` mit `path`) oder mit Sync in ein Datenbank-Projekt lesen.
  Diese Backups werden nicht automatisch gelöscht; `configs/backups/` steht in der
  `.gitignore`.
- Automatisches Backup der Datenbank: Vor einer Schema-Migration (nur wenn schon
  eine ältere Datenbank mit Schema existiert, nicht bei einer neuen, leeren) und
  vor einem Sync, der in die Datenbank schreibt (nicht bei der Vorschau, nicht
  beim Schreiben in den Markdown-Ordner, nicht wenn nichts zu ändern ist) legt der
  Dienst eine konsistente Kopie der SQLite-Datei an:
  `<CONFIG_DIR>/backups/todo-<JJJJMMTT-HHMMSS>-<migration|sync>.db` (zwei in
  derselben Sekunde: Zusatz `-2`, …). Es ist die SQLite-Backup-Funktion, daher
  auch im laufenden Betrieb (WAL) vollständig; die Kopie wird auf
  `integrity_check` und gleiche Zeilenzahlen je Tabelle geprüft und liegt ohne
  `-wal`/`-shm` da. Aufbewahrt werden die letzten 10 dieser Dateien (zusätzlich das jüngste je Tag der letzten 14 Tage), ältere
  automatische werden entfernt; der Grund `auto` gehört dem Auto-Sync; andere Dateien im Ordner (auch von Hand angelegte
  Kopien) bleiben unberührt. Scheitert die Sicherung, wird nichts migriert bzw.
  synchronisiert: der Sync antwortet 409 `database_backup_failed`
  (`details.reason`); die Migration läuft träge beim ersten Zugriff, die erste
  Anfrage antwortet dann ebenfalls 409 und die nächste versucht es erneut.
  Wiederherstellen: Dienst stoppen, die Datei als `todo.db` nach `configs/`
  kopieren (alte `todo.db-wal` und `todo.db-shm` entfernen). Nur für SQLite.
- Erster Start nach dem Update von einer Version mit Projekten in
  `config.json`: Projekte und UI-Zustand werden in die Datenbank übernommen,
  alle `source_id`s ändern sich einmal (Agenten schlagen sie über den Pfad
  nach). Zurück zum alten Stand: älteres Image starten und `config.json.bak`
  sowie `ui_state.json.bak` zurückbenennen.
- Nach einem Update mit neuen Python-Abhängigkeiten (z. B. SQLAlchemy) lokal
  `.venv/bin/pip install -r src_old/backend/requirements-dev.txt`; das Image installiert
  sie beim Neubau selbst.
- Prüfungen laufen lokal über `scripts/check.sh` (ruff, mypy --strict,
  import-linter, pytest, tsc, eslint, vitest); es gibt keine CI.

## Neubau (EPIC-007): Container neben dem alten Viewer

Der Neubau läuft als eigener Dienst `todo-viewer-next` (Host-Port **5411**, im Container 5412) neben dem alten `todo-viewer` (Host-Port 5412, im Container 5411), bis zum Umstieg. Beide teilen `./configs` und `./logs`, haben aber eigene Dateien: der alte `todo.db`/`todo-viewer.log`, der Neubau `viewer.db` und `viewer.log`.

- **Image.** `server/Dockerfile` (gebaut vom Projektordner: `build: {context: ., dockerfile: server/Dockerfile}`): Stage 1 baut den Client (`node:22-alpine`, `npm ci --ignore-scripts`, `vite build`), Stage 2 (`python:3.11-slim`) installiert den Server (`pip install -c server/constraints.txt ./server`; die Versionen in `server/constraints.txt` sind die getesteten) und kopiert `client/dist`. Der Server liefert `/` (Oberfläche, `index.html` für jede Adresse der Oberfläche), `/api/…` (HTTP-API, Health: `GET /api/core/health`) und `/mcp` (MCP für LLMs). Ein `HEALTHCHECK` fragt die Health-Adresse.
- **Compose-Dienst.** `restart: unless-stopped`; Port nur an `127.0.0.1:5411` gebunden (API und MCP können alles ändern); Volumes `./configs` → `/app/configs` (`viewer.db`, `configs/backups`), `./logs` → `/app/logs` (`viewer.log`, JSON-Zeilen) und der Projekte-Ordner unter demselben Pfad wie auf dem Host (Spiegel-Ordner; `BROWSE_START` wie beim alten Dienst). Aufruf: `http://localhost:5411`.
- **Konfiguration im Container** (Umgebung gewinnt, siehe `neubau-server.md`, „Konfiguration“): `VIEWER_HOST=0.0.0.0`, `VIEWER_PORT=5412`, `VIEWER_DB=/app/configs/viewer.db`, `VIEWER_BACKUP_DIR=/app/configs/backups`, `VIEWER_LOG_DIR=/app/logs`, `VIEWER_STATIC_DIR=/app/client/dist`.
- **`./todo.sh next <befehl>`:** `start` (bauen, falls nötig, und im Hintergrund starten), `stop`, `restart`, `update` (neu bauen ohne Cache, Container ersetzen), `logs` (folgt `logs/viewer.log`, sonst Container-Ausgabe), `status` (Container und Antwort von `/api/core/health`). Die Befehle ohne `next` betreffen nur den alten Viewer (`down` beide).
- **Backups.** Die Datenbank sichert sich selbst nach `configs/backups/viewer-<Zeit>Z-<Grund>.db` (SQLite-Backup-API, auch im laufenden Betrieb): Grund `migration` (vor der ersten ausstehenden Migration einer nicht leeren Datenbank), `sync` (vor einem Abgleich, der die Datenbank ändert) und `import` (vor der Datenübernahme in eine bestehende Datei). Je Grund bleiben die **letzten 10**; ältere löscht der Dienst. Wiederherstellen: Container anhalten (`./todo.sh next stop`), die gewählte Sicherung nach `configs/viewer.db` kopieren (`-wal` und `-shm` daneben löschen), starten.
- **Logs.** `logs/viewer.log` (JSON je Zeile, mit Request-ID); Meldungen vor der Log-Einrichtung stehen in `docker compose logs todo-viewer-next`.
- **Daten übernehmen** (Umstieg, nur der Projektinhaber): `python -m viewer.app.import_legacy` (siehe `neubau-server.md`, „Datenübernahme aus dem alten Viewer“); erst mit `--dry-run`.
- **Prüfen.** `scripts/check-next.sh` (enthält die Systemtests des Servers als Prozess und von `todo.sh`); der Image-Test baut und startet das Image und braucht einen laufenden Docker-Daemon und `VIEWER_IMAGE_TEST=1`: `cd server && VIEWER_IMAGE_TEST=1 ../.venv/bin/pytest -c pyproject.toml --rootdir=. ../tests/implementation/system/ops/test_image.py` (übersprungen ohne Docker).

## Laufender Betrieb

- Starten/Stoppen über `./todo.sh` (siehe [README](../../README.md)).
- Status: `./todo.sh status`; Live-Log: `./todo.sh logs` (folgt `logs/todo-viewer.log`).
- Erreichbarkeit: `GET /api/v2/health` antwortet mit `{"status": "ok", "api": "2"}`,
  ohne Backlog-Dateien zu lesen.
- Das Frontend wird pro Anfrage gesucht: ein späteres `npm --prefix src_old/web run build`
  wird ohne Neustart ausgeliefert.

## Notes im Betrieb

- Speicherort: Topics, Notes, Links, Auslöser und Note-Dokumente liegen nur in
  der zentralen Datenbank (`configs/todo.db`), unabhängig von der Primärquelle
  der Projekte. Sie gehören zur Sicherung der Datenbank (siehe „Deployment“);
  die Backups beim Wechsel einer Primärquelle enthalten sie nicht, und ein
  Markdown-Ordner oder -Spiegel enthält keine Notes.
- Zeit: Zeitpunkte (Auslöser, Prüf-Datum, Topic-Termine) speichert und liefert
  die API in UTC. Die Oberfläche zeigt und erfragt sie in der Zeitzone des
  Browsers, also des Rechners, an dem man den Viewer bedient. Wer die API
  direkt aufruft, übergibt ISO 8601 mit Zeitzone.
- Kein Hintergrund-Takt: Ob eine Note fällig ist, wird beim Lesen berechnet. Das
  Ausrufezeichen fragt den Zähler jede Minute und beim Fokussieren des Fensters
  ab; ein stehender Viewer ohne offenes Fenster kostet nichts und meldet nichts.
- Prüf-Intervall und Topic-Tiefe stehen in `config.json` (`notes.review_days`,
  `notes.max_topic_depth`, siehe [Konfiguration](configuration.md)) und wirken
  ohne Neustart.
- Nicht erreichbare Projekte: Zeigt ein Link oder Auslöser auf ein Projekt, das
  nicht (mehr) eingetragen oder nicht lesbar ist, bleibt er stehen und wird als
  nicht erreichbar markiert; der Server legt einmalig einen Hinweis
  `project_unreachable` an. Es entsteht kein Fehler, und der Hinweis
  bleibt auch nach der Rückkehr des Projekts offen, bis man ihn entscheidet.
- Endgültig löschen: Es gibt kein endgültiges Löschen von Notes und Topics über
  HTTP; der Papierkorb wird nur im Service für den Besitzer geleert.

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
| Seite zeigt „Frontend not built“ (HTTP 503) | `src_old/web/dist/index.html` fehlt (lokaler Start ohne Build) | `npm --prefix src_old/web run build` |
| Projekt in der Liste ausgegraut mit ⚠ | Backlog-Ordner fehlt, ist kein Ordner, enthält keine `TODO.md` oder ist im Container nicht eingebunden | Pfad in der UI korrigieren (⚙ → Projekte → „Ordner ändern…“); Ordner muss unter dem gemounteten Pfad liegen |
| Speichern bricht mit Hinweis auf externe Änderung ab (`version_conflict`/`file_changed`) | Der Eintrag wurde seit dem Lesen geändert bzw. die Datei während des Schreibens, z. B. durch einen Agenten | Nach dem nächsten Polling erneut bearbeiten |
| Projekt mit ⚠ „nicht im Backlog-Format“ (`unsupported_format`) | `TODO.md` ohne Format-Kennung, z. B. eine einfache Checkliste | Datei ins Backlog-Format überführen (Kennung und IDs) |
| Speichern schlägt mit `write_failed` fehl | Keine Schreibrechte auf den Backlog-Ordner | Rechte bzw. Volume-Mount (beschreibbar) prüfen |
| Ein Test meldet veraltete API-Typen | v2-API geändert, `openapi.json`/`schema.d.ts` nicht neu erzeugt | `.venv/bin/python src_old/backend/scripts/export_openapi.py && npm --prefix src_old/web run gen:api` |
| Sync bricht mit `sync_stale` ab | Seit der Vorschau hat sich die Datenbank oder der Ordner geändert (oder es fehlt das `token`) | Vorschau neu holen und bestätigen |
| Sync bricht mit `sync_source_invalid` ab (`details.reason`) | Der Sync-Ordner fehlt (`not_found`), hat keine `TODO.md` (`no_todo`) oder ist kein Backlog (`unsupported_format`, `parse_error`); es wurde nichts geändert | Ordner bzw. Datei reparieren, Vorschau wiederholen |
| Umstellen des Speicherorts mit `sync_required` abgelehnt | Beide Seiten sind nicht gleich (z. B. ein offener Konflikt oder ein Eintrag, den die Richtung ausschloss) | Sync mit Vorschau ausführen, Konflikte entscheiden, dann erneut umstellen |
| Sync meldet Konflikte, die nicht verschwinden | Ein Konflikt bleibt ohne Entscheidung auf beiden Seiten unberührt und wird wieder gemeldet | Je Konflikt `database` oder `markdown` entscheiden, oder beide Seiten von Hand gleich machen |
| Sync (Löschen per Entscheidung) bricht mit `lifecycle_violation` ab | Andere Items verweisen auf den Eintrag, der gelöscht werden soll | Verweise lösen oder die andere Seite entscheiden; es wurde nichts geändert |
| 409 `database_backup_failed` beim Sync oder bei der ersten Anfrage nach einem Update | Die Sicherung der Datenbank vor Sync oder Migration schlug fehl (Ordner `configs/backups/` nicht beschreibbar, Platte voll) | Ursache beheben und wiederholen; bis dahin wird nichts migriert oder synchronisiert |
| Datenbank-Projekt mit ⚠ `db_unavailable` | Die Datenbank lässt sich nicht öffnen (Datei gesperrt, `storage_url` falsch, Server nicht erreichbar); Log: `database_unavailable` | `storage_url` und Datei bzw. Dienst prüfen |
| Datenbank-Projekt lässt sich nicht austragen (`project_not_empty`) | Es hat noch Items | Zuerst auf Markdown ablegen (Umstellen) oder die Items löschen |
