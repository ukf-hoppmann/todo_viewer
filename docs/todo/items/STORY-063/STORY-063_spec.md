# `STORY-063` — Infrastruktur Datenbank

Grundlage: `EPIC-007_spec.md`, Abschnitte 5, 7.1.

## Umfang

- `viewer.core.infrastructure.database`: Engine (SQLite,
  `PRAGMA foreign_keys=ON`), Unit-of-Work/Transaktion als Port
  `Transaction` in `application`, Migrationslauf je Besitzer.
- Migration = `(version: int, apply: Callable[[Connection], None])`;
  Reihenfolge Core, dann Plugins topologisch nach `requires`.
- Tabellen des Core: `core_migrations(owner, version)`,
  `core_ui_state(owner, document, updated_at)`,
  `core_sync_state(project_uid, uid, hash, synced_at)` (genutzt von `STORY-065`).
- Prüfung beim Start: Tabellen eines Plugins tragen sein Präfix;
  Fremdschlüssel zeigen nur auf eigene Tabellen, Core oder `requires`.
- Backups: Port `BackupMaker`, Datei `configs/backups/viewer-<Zeit>-<grund>.db`,
  die letzten 10 je Grund bleiben.
- Optimistische Sperre: Hilfsfunktion für `revision`-Spalten
  (`UPDATE … WHERE revision = ?`, sonst `version_conflict`).
- UI-Zustand: Endpunkte aus `STORY-061` an die DB anschließen.

## Nicht im Umfang

Fachliche Tabellen (kommen mit den Plugins).

## Tests

Test zuerst: Migrationslauf (leer → aktuell, zweiter Lauf ändert nichts),
Präfix- und Fremdschlüssel-Prüfung, Revision-Konflikt, Backup-Rotation —
gegen echte SQLite-Dateien in einem temporären Ordner (Integration).
