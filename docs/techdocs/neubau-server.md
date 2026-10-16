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

## MCP

`/mcp` ist ein MCP-Server (Streamable HTTP, `mcp` 2.x) im selben Prozess. Jede Operation mit `mcp=True` ist ein Tool
`<owner>_<name>` (Bindestriche der ID als `_`): Beschreibung aus `summary`, Eingabe-Schema aus der Input-Dataclass
(dasselbe `TypeAdapter`-Schema wie die HTTP-Route), `read_only_hint` für `kind="read"`, Ausgabe als JSON-Text. Fehler
sind Tool-Ergebnisse mit `isError` und dem JSON `{code, message, details}` — derselbe Inhalt wie die HTTP-Fehlerantwort;
ungültige Argumente haben `validation_error`, ein unbekanntes Tool `not_found`. Erlaubte Hosts: `127.0.0.1`,
`localhost`, `[::1]` und `todo.localhost` (Schutz vor DNS-Rebinding).

## Konfiguration

`configs/viewer.json` (optional) und Umgebungsvariablen; die Umgebung gewinnt.

| Schlüssel (Datei) | Umgebung | Typ | Standard | Wirkung |
|---|---|---|---|---|
| `host` | `VIEWER_HOST` | String | `127.0.0.1` | Bind-Adresse (nur lokal laut Architektur) |
| `port` | `VIEWER_PORT` | Integer | `5412` | HTTP-Port des Neubaus |
| `log_dir` | `VIEWER_LOG_DIR` | Pfad | `logs` | Ordner mit `viewer.log` (JSON-Zeilen) |
| `sse_keepalive_seconds` | – | Zahl | `15` | Abstand der Keep-alive-Zeilen |
| `plugins.<id>` | – | Objekt | `{}` | Einstellungen eines Plugins (`context.settings`) |
| – | `VIEWER_CONFIG` | Pfad | `configs/viewer.json` | andere Konfigurationsdatei |

## Betrieb in der Entwicklung

```bash
PYTHONPATH=server/src .venv/bin/python -m viewer.app.main    # Port 5412
scripts/check-next.sh                                         # ruff, mypy, import-linter, pytest
```
