# Konfiguration

<!-- Jede Einstellung mit Typ, Standardwert, ob sie Pflicht ist, und ihrer Wirkung. -->

Der Server liest `configs/viewer.json` (optional) und Umgebungsvariablen. Die Umgebung gewinnt. Im Container setzt
`docker-compose.yml` die nötigen Werte (siehe [Betrieb](operations.md)).

## Server

| Einstellung (Datei) | Umgebungsvariable | Typ | Standard | Pflicht | Wirkung |
|---|---|---|---|---|---|
| `host` | `VIEWER_HOST` | String | `127.0.0.1` (im Container `0.0.0.0`) | nein | Adresse, an die der Server bindet. Nach der Architektur nur lokal; im Container schützt Compose, indem es den Port nur an `127.0.0.1` des Hosts bindet |
| `port` | `VIEWER_PORT` | Integer | `5411` | nein | HTTP-Port (API, Oberfläche, MCP) |
| `db_path` | `VIEWER_DB` | Pfad | `configs/viewer.db` | nein | SQLite-Datei mit allen Projekten, Items, Memos, Weckern und Mindmap-Knoten |
| `backup_dir` | `VIEWER_BACKUP_DIR` | Pfad | `configs/backups` | nein | Ordner der automatischen Datenbank-Sicherungen |
| `log_dir` | `VIEWER_LOG_DIR` | Pfad | `logs` | nein | Ordner mit `viewer.log` (JSON-Zeilen, rotiert) |
| `static_dir` | `VIEWER_STATIC_DIR` | Pfad | `client/dist` | nein | Gebaute Oberfläche, die der Server unter `/` ausliefert; fehlt der Ordner, gibt es nur die API |
| `auto_sync_interval_seconds` | `AUTO_SYNC_INTERVAL` | Zahl (Sekunden) | `30` | nein | Takt des Auto-Syncs; `0` schaltet ihn ab. Der Timer läuft nur, solange ein Projekt den Auto-Sync an hat. Zur Laufzeit in der Oberfläche änderbar (Einstellungen → System → Auto-Sync), außer die Umgebungsvariable ist gesetzt: sie gewinnt, das Feld ist dann gesperrt |
| `sse_keepalive_seconds` | – | Zahl | `15` | nein | Abstand der Keep-alive-Zeilen im Ereignisstrom |
| `plugins.<id>` | – | Objekt | `{}` | nein | Einstellungen eines Plugins |
| – | `VIEWER_CONFIG` | Pfad | `configs/viewer.json` | nein | Andere Konfigurationsdatei |
| – | `TZ` | IANA-Name (`Europe/Berlin`) | leer (dann UTC, Warnung im Log) | nein | Zeitzone des Rechners. Die Wecker rechnen ihre Serientermine darin; ohne sie verschieben sich Termine um die Sommerzeit. `todo.sh` gibt die Zone des Rechners an den Container weiter, Compose hat `Europe/Berlin` als Rückfall |
| – | `BROWSE_START` | Pfad | Home-Ordner | nein | Startordner des Ordner-Browsers beim Einrichten eines Spiegel-Ordners. In `docker-compose.yml` auf den Projekte-Ordner des Hosts gesetzt |
| – | `PYTHON_BIN` | Pfad | `.venv/bin` | nein | Nur `scripts/check-next.sh`: Ordner mit ruff, mypy, lint-imports, pytest |

Unbekannte Schlüssel in `viewer.json` bleiben beim Schreiben erhalten. Fehlt die Datei, gelten die Standardwerte.

## Einstellungen in der Oberfläche

Das Zahnrad (Tab „Einstellungen“) hat zwei Gruppen. Die offene Gruppe steht in der Adresse (`/core/settings?group=…`).

| Gruppe | Abschnitt | Wirkung |
|---|---|---|
| Projekte | Projektliste | Je Projekt Name, Spiegel-Ordner, Spiegel an/aus, Auto-Sync, Sync-Richtung; Stand des Spiegels und Sync-Dialog |
| System | Memos | Prüf-Intervall (Tage) und größte Topic-Tiefe |
| System | Wecker | Browser-Benachrichtigung bei fälligen Weckern |
| System | Auto-Sync | Takt in Sekunden (siehe oben) |

## UI-Zustand

Was man in der Oberfläche wählt (ausgeblendete Projekte, Filter, zugeklappte Knoten, gewähltes Item, Sprache DE/EN),
speichert der Server in der Datenbank, getrennt nach Besitzer (`core`, `workspace`, `backlog`, `memos`, `alarms`,
`mindmap`). Er wird nicht von Hand gepflegt und liegt nie im Browser-Speicher.
