# STORY-063 — Infrastruktur Datenbank: Migrationen je Plugin, Transaktionen, Backups

## 2026-10-16 — Entscheidungen

### Decided

- Die DB speichert rein relational; das Schema ist fest, keine freien Zusatzfelder. Neues kommt als Schemaänderung.
- Jedes Plugin hat eigene Tabellen und Migrationen; Fremdschlüssel nur auf Plugins aus requires.

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- Der Core bekommt wie ein Plugin eine `PluginDefinition` (Besitzer `core`) mit eigenen Migrationen und den beiden Operationen für den UI-Zustand; so entstehen deren Routen aus denselben Operationen wie alle anderen.
- Sync-Operationen (`sync`) sichern die Datenbank später über denselben Port `BackupMaker` (`STORY-065`); hier entsteht nur der Grund `migration`.
- SQLite führt DDL in pysqlite ohne `BEGIN` aus; damit jede Migration atomar ist, schaltet die Engine nach dem SQLAlchemy-Rezept auf eigenes `BEGIN` um.
- Auslegung „vor jeder Migration ein Backup“: ein Backup je Start, bevor die erste ausstehende Migration läuft (deckt alle ab). Eine leere Datenbank ohne Tabellen wird nicht gesichert, sonst würden die letzten 10 Sicherungen beim Erstanlauf mit leeren Dateien verdrängt. Siehe Frage 14 in `STORY-060`.
- Sync-Handler (sync) von Operationen laufen jetzt in einem Thread (`asyncio.to_thread`), damit blockierender Datenbankzugriff die Ereignisschleife (SSE, Scheduler) nicht anhält.

### Decided

1. **Domain**: `Migration(version, apply)`; Prüfung, dass Versionen je Besitzer lückenlos von 1 aufsteigen; Tabellen-Präfixe dürfen einander nicht überlappen; reine Funktion `schema_problems` (Präfix der eigenen Tabellen, Fremdschlüssel nur auf eigene, Core und `requires`). Tests zuerst.
2. **Engine und Transaktion**: `Database` (SQLite, `foreign_keys=ON`, eigenes `BEGIN`), Port `Transaction`/`Database` in `application`, Einstellungen `db_path`, `backup_dir`.
3. **Backups**: Port `BackupMaker`, Adapter mit der SQLite-Backup-API nach `configs/backups/viewer-<Zeit>-<grund>.db`, die letzten 10 je Grund bleiben.
4. **Migrationslauf**: je Besitzer in Abhängigkeitsreihenfolge, Stand in `core_migrations`, Backup vorher, jede Migration atomar, danach Präfix- und Fremdschlüsselprüfung; Core-Tabellen `core_migrations`, `core_ui_state`, `core_sync_state`.
5. **Optimistische Sperre**: Hilfsfunktion `update_with_revision` (`version_conflict`/`not_found`).
6. **UI-Zustand**: Operationen `get_ui_state`/`put_ui_state` des Core mit Speicher in `core_ui_state`; Verdrahtung in der Composition Root, Migrationslauf beim Start.
7. **Integration**: Tests gegen echte SQLite-Dateien in temporären Ordnern, Techdoku, `scripts/check-next.sh` grün.

### Open

- Keine.
