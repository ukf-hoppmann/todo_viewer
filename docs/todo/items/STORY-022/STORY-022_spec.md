# STORY-022 Spec: Projekte und UI-State in der zentralen DB

Gemeinsame Festlegungen und Schema: siehe `EPIC-003_spec.md`.

## Was und warum

Die Projektliste steht heute in `configs/config.json`, der UI-State in `ui_state.json`. Beides zieht in die DB, damit alles an einem Platz liegt. `config.json` behält nur `storage_url`.

## Entscheidungen

- `Source` bekommt `id` explizit (statt aus dem Pfad berechnet), `backend`, `path` (nur Markdown), `sync_path` (optional, Export-/Import-Ordner). `Source.id` für bestehende Quellen: der bisherige Hash; neue Projekte: UUID.
- Neue Adapter `DatabaseSourceRepository` (Port `SourceRepository`, `edit()` als Transaktion) und `DatabaseUiStateStore`. Der bisherige `JsonSourceRepository` bleibt für den Übergang bestehen, wird aber nur noch von der Migration gelesen.
- **Migration beim Start:** Existiert in `config.json` eine Liste `sources` und die DB hat keine Projekte, werden die Quellen als `backend=markdown` übernommen (gleiche `id`), `ui_state.json` wird importiert. Danach schreibt die Migration `config.json` ohne `sources` neu und legt vorher eine Sicherung `config.json.bak` an. Idempotent.
- **API:** Die bestehenden `/sources`-Endpunkte bleiben und werden um `backend` und `sync_path` erweitert (`SourceIn`/`SourceOut`). `POST /sources` mit Pfad legt weiter ein Markdown-Projekt an (der Harness-Helfer registriert Backlogs so und darf nicht brechen). Neu: Projekt mit `backend=database` anlegen (Name ohne Pfad); Backend-Wechsel eines Projekts gehört zur Sync-Story, nicht hierher.
- Duplikate: gleicher Name+Backend ist erlaubt, gleicher Markdown-`path` bleibt `duplicate`.

## Dateien

Geändert: `domain/source.py`, `application/services/sources.py`, `application/ports.py`, `api/v2/{routers,schemas}.py`, `bootstrap.py` (`Settings.storage_url`), `infrastructure/config/`. Neu: `infrastructure/database/{sources,ui_state}.py`, Migration für `projects`/`ui_state`.

## Abnahme

Bestehende Installation startet, übernimmt Quellen unverändert (gleiche `source_id`s, `backlog_api.py` funktioniert ohne neue Registrierung); Tests für Migration (mit/ohne `ui_state.json`, zweiter Start), CRUD der Projekte in der DB und `/sources`-Kompatibilität; OpenAPI und TypeScript-Typen regeneriert.

## Nicht Teil dieser Story

UI-Änderungen (STORY-024), Sync (STORY-023).
