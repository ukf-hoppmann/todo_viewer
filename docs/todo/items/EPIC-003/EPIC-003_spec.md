# EPIC-003 Spec: Wählbares Speicher-Backend

Gemeinsame Festlegungen für alle Stories des Epics. Die Stories verweisen hierauf.

## Ziel und Abgrenzung

Jedes Projekt (bisher `Source`) speichert wahlweise in Markdown-Dateien (`backend=markdown`, wie heute) oder in einer zentralen lokalen Datenbank (`backend=database`). Einzelnutzer, nur lokal. Sync zwischen beiden nur auf Knopfdruck oder API-Aufruf, keine automatische Spiegelung, kein Datei-Watcher. Der Domain-Code (Status, Archiv, Retype, Papierkorb) bleibt fachlich unverändert.

## Festlegungen

1. **Identität.** Ein Item hat in der DB eine `uid` (UUID, Primärschlüssel) und ein `label` (der heutige `Item.id`, z. B. `STORY-019`), eindeutig je Projekt. Beziehungen (Parent, Dependencies) und Dokumente verweisen auf die `uid`. Die Domäne und die HTTP-API adressieren Items weiter über das Label; `Item.id` bleibt das Label. Vorteil: Ein Typwechsel ändert nur die Spalte `label`, keine Verweise und keine Dokumentordner. In Markdown ist das Label wie bisher die ID.
2. **Projekt-Identität.** Projekte bekommen eine UUID als `id` (API: `source_id`). Beim Migrieren bestehender `config.json`-Quellen bleibt der bisherige 12-stellige Pfad-Hash als `id` erhalten, damit Registrierungen des Harness-Helfers (`backlog_api.py`) weiter greifen.
3. **Normalisierte Speicherung.** Die DB speichert Felder in Tabellen, nicht als Markdown-Text. Der Markdown-Export (`to_md`) rendert daraus über die vorhandenen Vorlagen und Renderer. Exportierte Dateien müssen nicht byte-gleich zu früheren Dateien sein, aber stabil: export → import → export ergibt identische Dateien, und der Import liefert dieselben Items (gleiche `Item.version`).
4. **Verbindung.** `config.json` enthält `storage_url` (Standard `sqlite:///configs/todo.db`, Zugangsdaten dürfen darin stehen, das Tool läuft lokal). Alles andere (Projekte, UI-State, Items, Dokumente) liegt danach in der DB.
5. **Sync-Löschungen.** Fehlende Einträge werden in der Vorschau als Warnung gemeldet und nur nach ausdrücklicher Bestätigung (`delete_missing=true`) gelöscht, in beide Richtungen.
6. **Fehlercodes** stabil, als `DomainError`-Unterklassen; Übersetzung im Frontend über den Code.

## Schema (Ziel, Details in STORY-021/022)

| Tabelle | Spalten (Auszug) |
|---|---|
| `projects` | `id`, `name`, `backend`, `path` (Markdown-Ordner), `sync_path` (Export-/Import-Ordner), `position` |
| `items` | `uid`, `project_id`, `label`, `type`, `title`, `status`, `parent_uid`, `required_for_parent`, `created`, `area`, `priority`, `goal`, `completion_criteria`, `summary`, `resolution`, `location`, `deleted`, `position` |
| `item_dependencies` | `item_uid`, `depends_on_uid`, `position` |
| `item_extra_fields` | `item_uid`, `key`, `value`, `position` |
| `documents` | `item_uid`, `kind` (`notes`\|`spec`), `topic` (NULL für die erste Datei), `content`, `position` |
| `ui_state` | `key`, `value` (JSON) |
| `schema_version` | `version` |

Der Dokumentname (`<Label>_notes.md`, `<Label>_spec.md`, `<Label>_spec_<Thema>.md`) wird aus Label, `kind` und `topic` abgeleitet, nicht gespeichert.

## Reihenfolge

STORY-019 → 020 → 021 → 022 → 023 → 024 → 025; STORY-026 (Postgres, optional) hängt nur an 021.
