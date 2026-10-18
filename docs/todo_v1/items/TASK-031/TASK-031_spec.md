# TASK-031 — Spec: Automatisches Datenbank-Backup vor Migration und Sync

## Arbeitsweise
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story. **Diese Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition`, `claude-harness:testing`, `claude-harness:techdocs`, `claude-harness:worktree`. Neues Verhalten: Test zuerst; er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Arbeit, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- **Datenbank-Backup zuerst (Vorgabe des Besitzers):** Bevor ein Schritt die echte Datenbank oder ihr Schema berührt, liegt ein frisches Backup in `configs/backups/` (bis TASK-031 fertig ist: von Hand mit der SQLite-Backup-Funktion `Connection.backup`, danach Integritätsprüfung und Zeilenzahlen vergleichen). Migrationen und Sync-Läufe werden zuerst an einer Kopie von `configs/todo.db` geprüft, nie zuerst an der echten Datenbank.
- Backlog: beim Start `In progress`, bei erfüllten Abschlusskriterien `Awaiting confirmation`.
- Weicht der Code von dieser Spec ab oder trifft die Arbeit auf einen Punkt unter „Stoppen und fragen“: nicht raten, anhalten und fragen.

## Ziel
Eine Sicherung der Datenbank, bevor etwas sie ändert, das sich nicht einfach zurücknehmen lässt: eine Schema-Migration und ein Sync in die Datenbank.

## Schon vorhanden
- Manuelles Vorbild (2026-10-14): konsistente Kopie mit `sqlite3.Connection.backup` nach `configs/backups/todo-<JJJJMMTT-HHMMSS>-<anlass>.db`, danach `pragma integrity_check` und Vergleich der Zeilenzahlen aller Tabellen.
- `configs/backups/` steht in `.gitignore`. Dort liegen auch die Backups beim Wechsel der Primärquelle (`application/services/backup.py`, Unterordner je Projekt) und eine ältere manuelle Kopie; sie bleiben unberührt.
- `infrastructure/database/engine.py`, `migrations.py` (versionierte `schema_version`), `application/services/sync.py` (`SyncService.run`).

## Festgelegt
- Nur SQLite (Postgres wurde verworfen, STORY-026).
- Dateiname `todo-<JJJJMMTT-HHMMSS>-<anlass>.db`, Anlass `migration` oder `sync`. Aufbewahrung: die letzten 10 Dateien dieser beiden Anlässe; andere Dateien im Ordner werden nie gelöscht.
- Konsistent im WAL-Betrieb über die SQLite-Backup-Funktion, kein Kopieren der Datei der laufenden Datenbank.
- Eine Sicherung nur, wenn tatsächlich etwas geändert würde: Migration ausstehend (eine neue, leere Datenbank braucht keine); Sync mit der Datenbank als Ziel (nicht bei Vorschau, nicht bei `to_md`).
- Scheitert die Sicherung, wird nichts migriert bzw. synchronisiert; stabiler Fehlercode `database_backup_failed` in der API-Fehlerform.
- Die Anwendungsschicht sieht nur einen Port (z. B. `DatabaseBackup` in `application/ports.py`); die SQLite-Umsetzung liegt in `infrastructure/database/`.

## Dateien
`application/ports.py`, `application/services/sync.py`, `application/container.py`, `bootstrap.py`, `infrastructure/database/engine.py`, `migrations.py`, neues Modul in `infrastructure/database/`, `domain/errors.py`, `api/errors.py`, Tests `backend/tests/{unit,integration,api_v2}`, Betriebsdoku `docs/techdocs/operations.md`.

## Nicht anfassen
Die Backups des Primärquellen-Wechsels, den Markdown-Adapter, das Schema der Tabellen.

## Tests (zuerst)
Mit festgelegter Uhr: Name und Aufbewahrung (11. Sicherung entfernt die älteste automatische, eine manuelle bleibt); Backup enthält auch Zeilen, die nur im WAL stehen; Sicherung vor ausstehender Migration, keine bei aktuellem Schema und keine bei leerer neuer Datenbank; Sicherung vor Sync mit Zieldatenbank, keine bei Vorschau und `to_md`; Fehler beim Sichern (Ordner nicht beschreibbar) → Datenbank und Spiegel unverändert, Fehlercode.

## Stoppen und fragen
Wenn die Migration beim Start läuft, bevor der Backup-Ordner bekannt ist; wenn eine fehlgeschlagene Sicherung den Start der Anwendung verhindern würde (Vorschlag: ja, der Start bricht mit klarer Meldung ab).

## Abnahme
Tests grün, `scripts/check.sh` grün; ein Probelauf an einer Kopie der echten Datenbank legt die erwartete Datei an.
