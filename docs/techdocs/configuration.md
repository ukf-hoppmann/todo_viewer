# Konfiguration

<!-- Jede Einstellung mit Typ, Standardwert, ob sie Pflicht ist, und ihrer Wirkung. -->

## Umgebungsvariablen

| Einstellung | Typ | Standard | Pflicht | Wirkung |
|---|---|---|---|---|
| `HOST` | String | `127.0.0.1` (im Docker-Image `0.0.0.0`) | nein | Adresse, an die uvicorn bindet |
| `PORT` | Integer | `5411` | nein | HTTP-Port |
| `DEV_RELOAD` | `0`/`1` | `1` (im Docker-Image `0`) | nein | Auto-Reload von uvicorn bei Code-Änderungen |
| `CONFIG_DIR` | Pfad | `<Projekt>/configs` | nein | Ordner mit `config.json` und `ui_state.json` |
| `FRONTEND_DIR` | Pfad | `<Projekt>/web/dist` | nein | Ordner mit dem gebauten Frontend |
| `BROWSE_START` | Pfad | Home-Ordner | nein | Startordner des Ordner-Browsers beim Hinzufügen von Projekten; wird ignoriert, wenn er kein Ordner ist. In `docker-compose.yml` auf `/Users/hoppmann/Documents/GitHub` gesetzt |
| `PYTHON_BIN` | Pfad | `.venv/bin` | nein | Nur `scripts/check.sh`: Ordner mit ruff, mypy, lint-imports, pytest |

## `configs/config.json`

| Einstellung | Typ | Standard | Pflicht | Wirkung |
|---|---|---|---|---|
| `sources` | Liste von Objekten | leer | ja (Datei fehlt → leerer Backlog) | Konfigurierte Backlog-Quellen |
| `sources[].project` | String | Name des umgebenden Git-Repos (beim Hinzufügen über die UI) | ja | Angezeigter Projektname |
| `sources[].path` | absoluter Pfad | — | ja | Backlog-Ordner mit `TODO.md`. Zeigt ein älterer Eintrag auf eine `.md`/`.markdown`/`.txt`-Datei, wird er beim Laden auf deren Ordner umgestellt und gespeichert |

Unbekannte Schlüssel auf oberster Ebene und in Quell-Einträgen bleiben beim
Schreiben erhalten. Änderungen an der Datei werden ohne Neustart übernommen.

## `configs/ui_state.json`

Wird von der UI geschrieben, nicht von Hand gepflegt.

| Einstellung | Typ | Standard | Pflicht | Wirkung |
|---|---|---|---|---|
| `hiddenProjects`, `hiddenStatuses`, `hiddenPriorities` | Liste von Strings | leer | nein | Ausgeblendete Filterwerte (englische Werte) |
| `collapsed` | Liste von Strings | leer | nein | Eingeklappte Knoten im Baum |
| `search` | String | leer | nein | Suchbegriff |
| `selectedId` | String oder `null` | `null` | nein | Ausgewähltes Item |
| `currentView` | `tree`/`graph`/`kanban` | `tree` | nein | Aktive Ansicht |
| `lang` | `de`/`en` | `de` | nein | Anzeigesprache |
