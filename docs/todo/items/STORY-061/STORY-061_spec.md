# `STORY-061` — Server-Grundgerüst

Grundlage: `EPIC-007_spec.md`, Abschnitte 3–6.

## Umfang

- `server/pyproject.toml` mit ruff, mypy `--strict`, import-linter
  (Verträge nach §4), pytest-Konfiguration für `tests/implementation/**/server`.
- `viewer.core`:
  - `domain`: `DomainError` mit `code`, `Event`, Plugin-Definition und
    `Operation` als Datentypen, Prüfung der Plugin-Liste (reine Funktionen).
  - `application`: Ports `Clock`, `EventBus`, `Scheduler`; Plugin-Host.
  - `infrastructure`: Systemuhr, EventBus im Prozess, Scheduler
    (asyncio, ein Termin je Besitzer), Konfiguration (`configs/viewer.json`
    + Umgebung), Logging (`logs/viewer.log`, Request-ID).
  - `api`: FastAPI-App, Routen aus Operationen (`pydantic.TypeAdapter` auf
    den Dataclasses), Fehler-Handler `{code, message, details}`,
    `GET /api/core/health`, `GET /api/core/events` (SSE, Keep-alive 15 s),
    `GET/PUT /api/core/ui-state/{owner}` (Speicher kommt mit `STORY-063`; bis dahin
    nicht verdrahtet).
- `viewer.app.composition`: feste Plugin-Liste, Verdrahtung;
  `viewer.app.main`: Start mit uvicorn, Port aus Konfiguration (Standard 5412).
- Ein Beispiel-Plugin nur für Tests unter `tests/helpers/server/example_plugin/`
  (nicht im Produktionscode).
- `scripts/check-next.sh`: ruff, mypy, import-linter, pytest für `server/`.

## Schnittstellen (fest)

- Plugin-Definition und `Operation` wie §6.
- Ereignis: `Event(topic: str, payload: dict, public: bool)`; nur
  `public` geht über SSE. SSE-Format: `event: <topic>` / `data: <json>`.
- `Scheduler.schedule(owner: str, at: datetime | None, callback)`; `None`
  löscht den Termin.

## Nicht im Umfang

MCP (`STORY-062`), Datenbank (`STORY-063`), Dateien (`STORY-064`), fachliche Plugins.

## Tests

Test zuerst für Plugin-Prüfung, Operation→Route, Fehlerumwandlung,
SSE-Weitergabe (Integration mit TestClient), Scheduler mit fester Uhr.
