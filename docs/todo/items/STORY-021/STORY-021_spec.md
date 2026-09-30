# STORY-021 Spec: SQLite-Adapter

Gemeinsame Festlegungen und Schema: siehe `EPIC-003_spec.md`.

## Was und warum

Ein Adapter `infrastructure/database/` implementiert `BacklogRepository` und `DocumentStore` gegen SQLite (SQLAlchemy Core, keine ORM-Modelle in der Domäne). Er wird über das Routing (STORY-020) für Projekte mit `backend=database` genutzt.

## Entscheidungen

- **Abhängigkeit:** SQLAlchemy 2.x in `backend/requirements.txt`; Migrationen als eigene, einfache Versionsliste (`infrastructure/database/migrations/`), Tabelle `schema_version`, kein Alembic. Beim Start werden fehlende Migrationen automatisch ausgeführt.
- **Mapping:** `Item.id` ↔ `items.label`; `parent`/`dependencies` werden beim Lesen von `uid` in Labels aufgelöst und beim Schreiben umgekehrt. `Item.version` bleibt der Hash über das Item (unverändert), Konfliktprüfung: gespeichertes Item laden, `version` vergleichen, sonst `VersionConflictError`.
- **Reihenfolge:** `position` je Projekt und `location`; neue Items ans Ende, verschobene Items ans Ende der Zielliste. Beim Laden nach `position` sortiert.
- **Papierkorb:** wie heute `location=archive` mit gesetztem `deleted`.
- **Retype:** `ChangeSet` mit neuem `id` ändert nur `label` (und `type`); Dokumente hängen an `uid`, `rename_item_folder` ist ein No-op, `delete_item_folder` löscht die Dokumente des Items.
- **Dokumente:** `read/write/append` parsen den Pfad `items/<Label>/<Label>_notes.md|_spec.md|_spec_<Thema>.md` in `(label, kind, topic)`; andere Pfade → `DocumentForbiddenError`. `content_version(text)` bleibt die Versionsbasis. `Item.notes`/`Item.spec` werden aus den vorhandenen Dokumenten abgeleitet.
- **Transaktionen:** `apply_all`, `delete`, `create` je in einer Transaktion. SQLite mit `PRAGMA foreign_keys=ON`, `journal_mode=WAL`.
- **Zusatzfelder:** unbekannte Felder aus `Item.extra_fields` in `item_extra_fields`.
- **`initialize`:** legt das Projekt leer an (keine Ordner); `check` liefert `SourceProblem("db_unavailable", …)` wenn die DB nicht erreichbar ist.

## Dateien

Neu: `infrastructure/database/{__init__,engine,schema,migrations/,repository,documents}.py`, `tests/contract/` (Fixture ergänzen), `tests/unit/infrastructure/test_database_*.py`. Geändert: `bootstrap.py` (Adapter + Routing), `pyproject.toml` (Layer-Vertrag), `requirements.txt`.

## Abnahme

Contract-Suite grün für Markdown, Fake und SQLite; Versionskonflikt, Duplikat-Label, Transaktions-Rollback und Migration (leere DB → aktuelle Version) getestet; ein Projekt mit `backend=database` lässt sich über die API lesen, anlegen, ändern, archivieren, löschen, wiederherstellen und mit Notizen/Specs versehen.

## Nicht Teil dieser Story

Projekte in der DB anlegen (STORY-022), Sync (STORY-023), Postgres (STORY-026).
