# Konfiguration

<!-- Jede Einstellung mit Typ, Standardwert, ob sie Pflicht ist, und ihrer Wirkung. -->

## Umgebungsvariablen

| Einstellung | Typ | Standard | Pflicht | Wirkung |
|---|---|---|---|---|
| `HOST` | String | `127.0.0.1` (im Docker-Image `0.0.0.0`) | nein | Adresse, an die uvicorn bindet |
| `PORT` | Integer | `5411` | nein | HTTP-Port |
| `DEV_RELOAD` | `0`/`1` | `1` (im Docker-Image `0`) | nein | Auto-Reload von uvicorn bei Code-Änderungen |
| `CONFIG_DIR` | Pfad | `<Projekt>/configs` | nein | Ordner mit `config.json` und (Standard) der Datenbank `todo.db` |
| `FRONTEND_DIR` | Pfad | `<Projekt>/web/dist` | nein | Ordner mit dem gebauten Frontend |
| `BROWSE_START` | Pfad | Home-Ordner | nein | Startordner des Ordner-Browsers beim Hinzufügen von Projekten; wird ignoriert, wenn er kein Ordner ist. In `docker-compose.yml` auf `/Users/hoppmann/Documents/GitHub` gesetzt |
| `LOG_FILE` | Pfad | leer (Konsole) | nein | Logdatei; wird nach Größe rotiert (5 MB, 5 alte Dateien `.1`–`.5`). Ohne Wert wird auf stderr geloggt. In `docker-compose.yml` auf `/app/logs/todo-viewer.log` gesetzt (Host: `./logs/`) |
| `LOG_LEVEL` | `DEBUG`/`INFO`/`WARNING`/`ERROR` | `INFO` | nein | Mindestlevel des Logs. `DEBUG` zeigt zusätzlich Lesezugriffe, Speichern des UI-Zustands und Stacktraces nicht lesbarer Backlogs; ein unbekannter Wert bricht den Start ab |
| `PYTHON_BIN` | Pfad | `.venv/bin` | nein | Nur `scripts/check.sh`: Ordner mit ruff, mypy, lint-imports, pytest |

## `configs/config.json`

| Einstellung | Typ | Standard | Pflicht | Wirkung |
|---|---|---|---|---|
| `storage_url` | SQLAlchemy-URL | `sqlite:///<CONFIG_DIR>/todo.db` | nein | Zentrale Datenbank. Sie enthält die Projektliste, den UI-Zustand und die Inhalte der Projekte mit `backend: database`. Wird beim Start gelesen (Änderung braucht einen Neustart); ein fehlender Ordner für die SQLite-Datei wird angelegt. Zugangsdaten dürfen in der URL stehen; sie werden nicht geloggt |

Unbekannte Schlüssel bleiben beim Schreiben erhalten. Fehlt die Datei, gilt
der Standard.

Ändert man `storage_url`, zeigt der Dienst danach auf eine andere (ggf. leere)
Datenbank; Projekte und Inhalte wandern nicht mit. Der Sync-Ordner eines
Datenbank-Projekts (`sync_path`) und alle anderen Projekteinstellungen stehen in
der Datenbank, nicht in dieser Datei.

Projekte stehen nicht mehr in dieser Datei, sondern in der Datenbank; sie
werden über die UI bzw. `/api/v2/sources` verwaltet (siehe
[Schnittstellen](interfaces.md)). Enthält `config.json` noch eine Liste
`sources` (frühere Versionen), wird sie beim ersten Zugriff übernommen:

- jedes Projekt bekommt eine neue UUID als `source_id`; Markdown-Ordner, die
  schon eingetragen sind, werden übersprungen;
- Einträge mit `"backend": "database"` ziehen samt ihren Items unter die neue
  ID um;
- ältere Einträge, die auf eine `.md`/`.markdown`/`.txt`-Datei zeigen, werden
  auf deren Ordner umgestellt;
- danach wird `config.json` ohne `sources` neu geschrieben; der vorherige
  Inhalt bleibt als `config.json.bak` erhalten.

## UI-Zustand

Wird von der UI über `/api/v2/ui-state` geschrieben und in der Datenbank
gespeichert, nicht von Hand gepflegt. Eine `configs/ui_state.json` früherer
Versionen wird beim ersten Zugriff übernommen (falls die Datenbank noch keinen
UI-Zustand hat) und in `ui_state.json.bak` umbenannt.

| Einstellung | Typ | Standard | Pflicht | Wirkung |
|---|---|---|---|---|
| `hiddenProjects`, `hiddenStatuses`, `hiddenPriorities` | Liste von Strings | leer | nein | Ausgeblendete Filterwerte (englische Werte) |
| `collapsed` | Liste von Strings | leer | nein | Eingeklappte Knoten im Baum |
| `markedProjects` | Liste von Strings | leer | nein | Markierte Projekte, auf die „Epics/Stories zuklappen/aufklappen“ wirken; leer = alle |
| `search` | String | leer | nein | Suchbegriff |
| `selectedId` | String oder `null` | `null` | nein | Ausgewähltes Item |
| `currentView` | `tree`/`graph`/`kanban`/`trash` | `tree` | nein | Aktive Ansicht |
| `lang` | `de`/`en` | `de` | nein | Anzeigesprache |
