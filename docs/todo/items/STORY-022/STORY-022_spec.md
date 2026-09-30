# STORY-022 Spec: Projekte und UI-State in der zentralen DB

Gemeinsame Festlegungen und Schema: siehe `EPIC-003_spec.md`.

## Was und warum

Die Projektliste steht heute in `configs/config.json`, der UI-State in `ui_state.json`. Beides zieht in die DB, damit alles an einem Platz liegt. `config.json` behält nur `storage_url`.

## Entscheidungen

- `Source` bekommt `id` explizit (UUID, statt aus dem Pfad berechnet), `backend`, `path` (nur Markdown), `sync_path` (optional, Export-/Import-Ordner; nur Datenbank). `Source.id` als Pfad-Hash entfällt; `updated()` behält die `id`.
- Neue Adapter `DatabaseSourceRepository` (Port `SourceRepository`, `edit()` als Transaktion) und `DatabaseUiStateStore`. Der bisherige `JsonSourceRepository` bleibt für den Übergang bestehen, wird aber nur noch von der Migration gelesen.
- **Übernahme beim ersten Zugriff** (`infrastructure/database/config_import.py`, nicht beim Start, damit Tests und Betrieb gleich laufen): Enthält `config.json` eine Liste `sources`, werden die Quellen mit neuer UUID übernommen; schon eingetragene Markdown-Ordner werden übersprungen, Datenbank-Quellen aus STORY-021 ziehen samt Items unter die neue ID um. Danach wird `config.json` ohne `sources` neu geschrieben, vorher entsteht `config.json.bak`. `ui_state.json` wird übernommen, wenn die DB noch keinen UI-Zustand hat, und in `ui_state.json.bak` umbenannt. Idempotent; die Datenbankdatei entsteht damit immer.
- **API:** Die bestehenden `/sources`-Endpunkte bleiben und werden um `backend` und `sync_path` erweitert (`SourceIn`/`SourceOut`). `POST /sources` mit Pfad legt weiter ein Markdown-Projekt an (der Harness-Helfer registriert Backlogs so und darf nicht brechen). Neu: Projekt mit `backend=database` anlegen (Name nötig, sonst `value_required`; `path` leer). `PUT` lehnt einen Backend-Wechsel mit `backend_change_not_supported` ab (Wechsel über den Sync, STORY-023). `DELETE` lehnt ein Datenbank-Projekt mit Items mit `project_not_empty` ab.
- **Keine Verzweigung nach Backend im Service:** den fehlenden Pfad meldet der Markdown-Adapter (`missing_path`); ein Name wird nur aus einem vorhandenen Ordner vorgeschlagen; Duplikate werden nur bei nicht leerem Pfad geprüft.
- Duplikate: gleicher Name+Backend ist erlaubt, gleicher Markdown-`path` bleibt `duplicate`.

## Dateien

Geändert: `domain/source.py`, `application/services/sources.py`, `application/ports.py`, `api/v2/{routers,schemas}.py`, `bootstrap.py` (`storage_url` aus `config.json`), `infrastructure/config/`. Neu: `infrastructure/database/{sources,ui_state,config_import}.py`, Migration v2 (Spalten in `projects`, Tabelle `ui_state`).

## Abnahme

Bestehende Installation startet und übernimmt die Quellen mit neuen UUIDs (`ui_state` bleibt gültig, da sie über Namen verweist; `backlog_api.py` findet die Projekte weiter über den Pfad); Tests für Migration (mit/ohne `ui_state.json`, zweiter Start), CRUD der Projekte in der DB und `/sources`-Kompatibilität; OpenAPI und TypeScript-Typen regeneriert.

## Nicht Teil dieser Story

UI-Änderungen (STORY-024), Sync (STORY-023).
