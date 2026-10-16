# STORY-061 — Server-Grundgerüst: Core mit Plugin-Host, HTTP, Ereignissen und SSE

## 2026-10-16 — Entscheidungen

### Decided

- Plugins aus einer festen Liste in der Composition Root, zunächst alle.
- Operationen werden einmal beschrieben; HTTP-Route und MCP-Tool werden daraus erzeugt.
- SSE ist der allgemeine Kanal vom Backend ins Frontend; die API ist der Weg vom Frontend ins Backend.
- Composition Root wie in my_story_game: dort werden die Operationen zusammengesteckt.

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- Plan nach der Zerlegungsregel, je Abschnitt ein Job, ein Test, ein Commit. Der letzte Abschnitt ist die Integration.
- Auslegung der Spec: `PluginDefinition`, `PluginContext` und der Plugin-Host liegen in `core/application` (sie brauchen die Ports); `core/domain` enthält `Operation`, `HttpBinding`, `Subscription`, `Migration`, `DomainError`, `Event`, `Settings` und die reine Prüfung der Plugin-Liste, die gegen ein Protokoll `PluginShape` arbeitet. Grund: `domain` darf keine Ports aus `application` kennen. Siehe Frage 13 in `STORY-060`.
- Ein Handler hat die Form `handler(services, input)`; `services` ist das Objekt, das `build(context)` des Plugins liefert. So kann eine Operation schon in der Definition stehen, obwohl die Dienste erst beim Start gebaut werden.

### Decided

1. **Gerüst**: `server/pyproject.toml` (ruff, mypy strict mit `python_version = "3.11"`, import-linter, pytest), `scripts/check-next.sh`, `tests/README.md`, Paketordner mit den vier Schichten.
2. **Domain**: `DomainError`, `Event`, `Operation`, Plugin-Datentypen, Prüfung der Plugin-Liste (unbekanntes `requires`, Zyklus, doppelte IDs, Operationen, Routen, Tools, Tabellen-Präfixe). Tests zuerst.
3. **Ports und Infrastruktur**: `Clock`, `EventBus`, `Scheduler`; Systemuhr, EventBus im Prozess, asyncio-Scheduler mit einem Termin je Besitzer.
4. **Plugin-Host**: sortiert nach `requires`, baut die Dienste, hängt Abonnements an den EventBus, führt Operationen aus.
5. **Konfiguration und Logging**: `configs/viewer.json` + Umgebung, structlog nach `logs/viewer.log` mit Request-ID.
6. **HTTP-Host**: Routen und OpenAPI aus den Operationen, Fehlerumwandlung `{code, message, details}`, `GET /api/core/health`.
7. **SSE**: `GET /api/core/events`, nur öffentliche Ereignisse, Keep-alive.
8. **Integration**: Composition Root, `main.py` (Port 5412), Beispiel-Plugin, Integrationstests gegen einen echten uvicorn-Server, `scripts/check-next.sh` grün, Techdoku.

### Open

- Keine.

## 2026-10-16 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Alle acht Plan-Abschnitte sind umgesetzt, je einer als Commit auf `neubau/epic-007`.
- Abweichungen von der Spec: `PluginDefinition` und `PluginContext` liegen in `core/application` (Frage 13 in `STORY-060`); das Beispiel-Plugin ist nur in den Tests, die Produktionsliste `PLUGINS` ist leer, bis die Plugin-Stories sie füllen. `GET/PUT /api/core/ui-state/{owner}` ist wie in der Spec nicht verdrahtet (kommt mit `STORY-063`).
- Fehler im OpenAPI-Schema: `ErrorBody` als Antwort `4XX` statt FastAPIs `HTTPValidationError`.

### Decided

- Abschlusskriterien geprüft: (1) `python -m viewer.app.main` startet und `GET /api/core/health` antwortet (Test `test_server_process_starts_and_answers_health`, Standardport 5412); (2) Operationen des Beispiel-Plugins sind als Routen erreichbar und im OpenAPI-Schema (`test_http_operations.py`); (3) ein öffentliches Ereignis kommt bei einem SSE-Client an, ein nicht öffentliches nicht (`test_sse.py`, echter uvicorn-Server); (4) unbekanntes `requires`, Zyklus und doppelte Route verhindern den Start (`test_plugin_validation.py`, `test_startup.py`); (5) vier import-linter-Verträge laufen grün.
- `scripts/check-next.sh` grün (ruff, mypy strict, import-linter, 52 Tests); `scripts/check.sh` des alten Viewers grün (1173 Backend-, 404 Frontend-Tests).
- Status: `Awaiting confirmation`.

### Open

- Keine.
