# STORY-021 Spec: SQLite-Adapter

Gemeinsame Festlegungen und Schema: siehe `EPIC-003_spec.md`.

## Was und warum

Ein Adapter `infrastructure/database/` implementiert `BacklogRepository` und `DocumentStore` gegen SQLite (SQLAlchemy Core, keine ORM-Modelle in der Domäne). Er wird über das Routing (STORY-020) für Projekte mit `backend=database` genutzt.

## Entscheidungen

- **Abhängigkeit:** SQLAlchemy 2.1 in `backend/requirements.txt`; Migrationen als eigene, einfache Versionsliste (`infrastructure/database/migrations.py`, SQL je Version), Tabelle `schema_version`, kein Alembic. Fehlende Migrationen laufen automatisch beim ersten Zugriff; vorher wird keine Datei angelegt.
- **Mapping:** `Item.id` ↔ `items.label`; `parent`/`dependencies` werden beim Lesen von `uid` in Labels aufgelöst und beim Schreiben umgekehrt. `Item.version` bleibt der Hash über das Item (unverändert), Konfliktprüfung: gespeichertes Item laden, `version` vergleichen, sonst `VersionConflictError`.
- **Reihenfolge:** `position` je Projekt und `location`; neue Items ans Ende, verschobene Items ans Ende der Zielliste. Beim Laden nach `position` sortiert.
- **Papierkorb:** wie heute `location=archive` mit gesetztem `deleted`.
- **Retype:** `ChangeSet` mit neuem `id` ändert nur `label` (und `type`); Ids ändern sich innerhalb eines `apply_all` zuerst, damit Verweise im selben Plan schon die neue ID nutzen. Dokumente hängen an der `uid`; `relabel_documents` benennt nur Namen um und findet das Item unter alter oder neuer ID (Rückbau bei fehlgeschlagenem Typwechsel).
- **Dokumente:** Der Port ist seit STORY-027 itembasiert (Item-ID und Name). Tabelle `documents(item_uid, name, content)`; Namen ohne `/`, nur `.md`/`.markdown`/`.txt`. Die Listen `Item.notes`/`Item.spec` stehen getrennt in `item_document_names` (Reihenfolge). Für Items, die es nicht gibt, speichert die Datenbank keine Dokumente (`ItemNotFoundError`). `content_version(text)` bleibt die Versionsbasis.
- **Verweise:** `parent`/`dependencies` sind Fremdschlüssel auf `items.uid`, geprüft beim Commit. Verweise auf unbekannte Items lehnt der Adapter mit `unknown_reference` ab; Löschen eines Items, auf das noch verwiesen wird, mit `item_referenced`.
- **`store_all(source, items)`:** nur am Datenbank-Adapter (nicht im Port): ersetzt alle Items eines Projekts in einer Transaktion. Wird von den Tests genutzt; STORY-023 (Sync) entscheidet, ob er in den Port kommt.
- **Transaktionen:** `apply_all`, `delete`, `create` je in einer Transaktion. SQLite mit `PRAGMA foreign_keys=ON`, `journal_mode=WAL`.
- **Zusatzfelder:** unbekannte Felder aus `Item.extra_fields` in `item_extra_fields`.
- **`initialize`:** legt das Projekt leer an (keine Ordner); die Projektzeile entsteht sonst beim ersten Schreiben. `check`/`load` liefern `SourceProblem("db_unavailable", …)`, wenn die DB nicht geöffnet werden kann.
- **Projekte bis STORY-022:** eine Quelle in `config.json` mit `"backend": "database"`; `path` ist der Projektschlüssel, Projekt-ID in der DB ist `Source.id`. Die Verbindung steht als `storage_url` in `config.json` (Standard `sqlite:///<config_dir>/todo.db`), keine Umgebungsvariable. Anlegen und Ändern solcher Quellen über die UI/API kommt mit STORY-022.

## Dateien

Neu: `infrastructure/database/{__init__,engine,schema,migrations,repository,documents}.py`, `tests/contract/` (Fixture ergänzen), `tests/unit/infrastructure/test_database_*.py`. Geändert: `bootstrap.py` (Adapter + Routing), `pyproject.toml` (Layer-Vertrag), `requirements.txt`.

## Abnahme

Contract-Suite grün für Markdown, Fake und SQLite; Versionskonflikt, Duplikat-Label, Transaktions-Rollback und Migration (leere DB → aktuelle Version) getestet; ein Projekt mit `backend=database` lässt sich über die API lesen, anlegen, ändern, archivieren, löschen, wiederherstellen und mit Notizen/Specs versehen.

## Nicht Teil dieser Story

Projekte in der DB anlegen (STORY-022), Sync (STORY-023), Postgres (STORY-026).
