# Übergabe an die Cloud-Sitzung: Abgleich (Sync) in drei Blöcken

Stand 2026-10-15. Dieses Dokument und `ergebnis.md` sind Übergabe-Arbeitsdateien; der Besitzer entfernt sie nach dem Merge. Sie gehören nicht zum Produkt.

## Auftrag
Der Besitzer hat beauftragt, drei Blöcke **hintereinander** in dieser Cloud-Sitzung umzusetzen. Hintergrund: Backlog und Notes sollen über Git zwischen Rechnern und der Cloud (claude.ai) wandern, ohne dass der Sync etwas still überschreibt, und ein abschaltbarer Auto-Sync soll das Nachziehen nach einem Pull übernehmen.

| Block | Items (in dieser Reihenfolge) | Branch (gestapelt) |
|---|---|---|
| **A** Abgleich pro Eintrag | STORY-057 mit TASK-031 (Datenbank-Backup), TASK-032 (Stand je Eintrag), TASK-033 (Konflikte entscheiden) | `cloud/block-a-abgleich-pro-eintrag` ab `cloud/abgleich-bloecke` |
| **B** Dialog und Auto-Sync | STORY-058 (Konflikt-Dialog mit Diff-Ansicht), STORY-059 (Auto-Sync, abschaltbar) | `cloud/block-b-dialog-auto-sync` ab Block A |
| **C** Notes im Sync | STORY-047 mit TASK-024 (Dateiformat), TASK-025 (Spiegel-Adapter), TASK-026 (Notes im gemeinsamen Sync), TASK-027 (Notes im Sync-Dialog) | `cloud/block-c-notes-im-sync` ab Block B |

Abhängigkeiten: TASK-031 → TASK-032 → TASK-033; STORY-058 und STORY-059 brauchen STORY-057; TASK-024 → TASK-025 → TASK-026 (braucht auch TASK-033) → TASK-027 (braucht auch STORY-058).

## Was du zuerst liest
1. `docs/development/architecture.md` **vollständig**, dazu `architecture/backend.md` und `architecture/web.md`. §1 (Sync, Abgleich pro Eintrag, Auto-Sync) und §3 (Timer-Ausnahme) hat der Besitzer am 2026-10-14 geändert und freigegeben. Sie sind verbindlich.
2. Die Specs: `docs/todo/items/<ID>/<ID>_spec.md` und `<ID>_notes.md` der Items oben; die Einträge (Ziel, Abschlusskriterien) stehen in `docs/todo/TODO.md`. **Die Spec legt den Umfang fest; was dort nicht steht, gehört nicht dazu.** Die Abschnitte „Stoppen und fragen“ gelten.
3. Dieses Dokument.

## Umgebung und Regeln
- Du hast hier **keinen Zugriff** auf den ToDo-Viewer (`localhost:5411`), auf die echte Datenbank (`configs/todo.db`, nicht im Git) und vermutlich nicht auf das Harness-Plugin (Skills und Hooks). Die Specs verweisen auf Skills wie `claude-harness:decomposition`; ohne Plugin gelten stattdessen die Regeln unten und in `architecture.md`.
- **Das Backlog nicht anfassen:** nicht `docs/todo/**` ändern, keine Status, keine Notes. Der Besitzer trägt alles lokal nach. Der heutige Sync würde sonst beim Einlesen ganze Seiten überschreiben, genau das, was STORY-057 beheben soll. Was ins Backlog gehört, schreibst du in `docs/handover/ergebnis.md` (Vorlage dort).
- **Setup und Basislauf vor jeder Änderung:** `python3 -m venv .venv && .venv/bin/pip install -r backend/requirements-dev.txt`, dann `cd web && npm ci`, dann `scripts/check.sh` (ruff, mypy `--strict`, import-linter, pytest, tsc, eslint, vitest). Läuft der Basislauf nicht grün oder lässt sich nichts installieren: **anhalten und melden**, nichts überspringen.
- **Tests** liegen unter `backend/tests/{unit,integration,api_v2,contract,characterization}` und `web/src/**/*.test.ts(x)`; das ist der bestehende Aufbau (die `tests`-Angabe der Harness-Konfig zeigt auf einen Ordner, den es nicht gibt). Neues Verhalten mit klarer Schnittstelle: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen. Testdaten sind synthetisch (`backend/tests/fixtures`), nie echte Daten. Datenbanken in Tests liegen als Datei in `tmp_path`.
- **API-Schema:** ändert es sich, `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `openapi.json` und `schema.d.ts` nie von Hand.
- **Migrationen** nur vorwärts, in `backend/todo_viewer/infrastructure/database/migrations.py` (`MIGRATIONS`, die höchste Version ist heute 7; eine neue ist die nächste Nummer). Es braucht einen Test, der von der Vorversion hochmigriert. **Die echte Datenbank wird nie berührt.** Die Migration an einer Kopie der echten Datenbank prüft der Besitzer lokal nach einem Backup.
- **Fehler** als `DomainError`-Unterklassen mit stabilem `code` (`domain/errors.py`); `ConflictError` wird in `api/errors.py` zu 409. Das Frontend übersetzt über `err.<code>` in `web/src/i18n/messages.ts` (Deutsch und Englisch).
- **Doku:** ändert eine Änderung Verhalten, Schnittstellen, Konfiguration oder Betrieb, aktualisierst du im selben Branch `docs/techdocs/{architecture,interfaces,configuration,operations}.md` und `README.md`. Die Specs nennen die Stellen.
- **Pläne:** Stelle je Block selbst einen Plan nach diesen Regeln auf: Abschnitte, die je **eine** Aufgabe haben, **allein testbar und allein integrierbar** sind (danach baut alles, alle Tests laufen), Schnittstellen zwischen den Abschnitten vorab festgelegt, letzter Abschnitt = Integration. Der Besitzer hat die Umsetzung aller drei Blöcke beauftragt; **warte nicht auf eine Planfreigabe**, halte den Plan in `ergebnis.md` fest.
- **Anhalten und den Besitzer fragen**, wenn: ein Punkt unter „Stoppen und fragen“ einer Spec eintritt; Code oder Realität von Spec oder Architektur abweichen; sich Anforderungen widersprechen; eine neue Abhängigkeit (pip oder npm) nötig wäre (für die Diff-Ansicht in STORY-058 zuerst eine eigene Zeilenvergleichsfunktion in `web/src/domain/` prüfen); eine Architekturregel geändert werden müsste.
- **Git:** pro Block ein Branch (siehe Tabelle), gestapelt. Kleine, thematisch geschlossene Commits mit deutscher Kurzbeschreibung und der Zeile `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Nicht nach `main` pushen, nichts mergen, kein Force-Push. Je Block ein Pull Request gegen den vorigen Branch (Block A gegen `cloud/abgleich-bloecke`).
- **Nicht in die Cloud gehört:** Migration der echten Datenbank, Deployment (`./todo.sh update`), UI-Sichtprüfung mit Screenshot (hier nur Komponententests), Backlog-Pflege, Tagesbericht und SemVer-Release. Das macht der Besitzer lokal nach dem Merge.

## Vom Besitzer entschieden
- **Beidseitiger Abgleich pro Eintrag** (Variante A): nur in der Datenbank geändert → Datei; nur in der Datei geändert → Datenbank; auf einer Seite neu → auf die andere. `direction` bleibt nur als Einschränkung („nur diese Richtung ausführen“).
- **Konflikte** (beide Seiten geändert, beidseitig neu mit verschiedenem Inhalt, auf einer Seite gelöscht) werden gemeldet und nie überschrieben oder gelöscht. Entscheidung je Konflikt: `database`, `markdown` (die Seite, deren Zustand gelten soll) oder aufschieben. **Aufschieben hat keinen eigenen Zustand**: ein nicht entschiedener Konflikt bleibt unberührt und wird beim nächsten Abgleich wieder gemeldet. Ein Konflikt ohne Entscheidung gilt als aufgeschoben.
- **Löschungen sind Konflikte.** `delete_missing` entfällt (Vorschlag aus den Specs; bleibt es nötig, begründen).
- **Kein automatischer Merge** innerhalb eines Eintrags. Je Eintrag wird nur die Version (Hash) gespeichert, kein Inhalt.
- **Backup:** vor jeder Schema-Migration und vor jedem Sync, der in die Datenbank schreibt (TASK-031, SQLite-Backup-Funktion, Aufbewahrung die letzten 10 automatischen). Der Auto-Sync braucht später eine zeitbasierte Aufbewahrung (siehe STORY-059-Spec).
- **Auto-Sync:** pro Projekt ein- und ausschaltbar, Standard aus; überträgt nur Konfliktfreies, löscht nie, liest keine unlesbaren Dateien oder Dateien mit Git-Merge-Markern, wartet einen laufenden Pull ab, sichert vor Datenbank-Schreibzugriffen; läuft nur, solange mindestens ein Projekt den Schalter an hat.
- **Notes im selben Sync wie der Backlog** (eine Vorschau, ein Status, ein Konflikt-Dialog). In der Cloud neu angelegte Notes haben kein Label (`new-<kurzname>.md`); die Datenbank vergibt es beim Import. Papierkorb-/Archivstand, `fired_at`, `already_met`, `Created`/`Updated` und die Label-Zähler wandern mit, Änderungshinweise (`note_notices`) nicht. Der Datei-Adapter liegt in `infrastructure/notes_files/`, nicht in `infrastructure/markdown/` (Import-Linter).

## Analysestand aus der lokalen Sitzung (zum Prüfen, nicht bindend)
- `Database.begin()` in `infrastructure/database/engine.py` migriert **träge** beim ersten Zugriff, nicht beim Start. Ein Backup-Fehler vor der Migration zeigt sich deshalb als 409 bei der ersten Anfrage.
- Der Sync ist `SyncService.run` in `application/services/sync.py` (Konstruktor `SyncService(backlogs, documents, listener=None)`; Tests bauen ihn so in `backend/tests/integration/test_sync.py`, `test_sync_status.py`, `test_backup.py`). Reine Logik in `domain/sync.py` (`plan_sync`, `classify`, `fingerprint`, `merged_items`, `check_token`). Heute kennt der Sync nur den Stand ganzer Seiten (`Source.baseline`, Spalten `synced_primary`/`synced_mirror` in `projects`); `plan_sync` vergleicht Items über ihre ID und Version, `merged_items` lässt Zielseiten-Einträge stehen oder löscht sie mit `delete_missing`.
- Backup-Idee für TASK-031 (Vorschlag): `domain/database_backup.py` mit `backup_file_name(at, reason, attempt)` → `todo-JJJJMMTT-HHMMSS-<anlass>.db` und `backups_to_remove(names, keep=10)` (nur Namen nach Muster); Port `DatabaseBackup.create(reason) -> str | None`; Adapter `SqliteFileBackup` mit `sqlite3.Connection.backup` (konsistent im WAL-Betrieb), am Ziel `PRAGMA journal_mode=DELETE` damit keine `-wal`/`-shm` bleiben, Prüfung `integrity_check`; `Database(url, before_migration=…)` plus `migrations.has_pending`; `SyncService(..., db_backup=None)`; Fehler `DatabaseBackupFailedError`, Code `database_backup_failed`. Backup-Ordner `<config_dir>/backups/`, derselbe wie beim Wechsel der Primärquelle; andere Dateien dort nie löschen.
- Frontend: `web/src/components/SyncDialog.tsx`, `domain/sync.ts`, `settings/ProjectsSection.tsx`, Hooks in `api/queries.ts`, Texte in `i18n/messages.ts`. Ein bestehender Test zeigt, wie Fehlercodes im Dialog geprüft werden (`sync.test.tsx`, Fall `backup_failed`).
- Der Spiegel des Projekts liegt in `docs/todo/`; die Sync-API ist `POST /api/v2/sources/{id}/sync` und `GET /api/v2/sources/{id}/sync-status`.

## Abschluss jedes Blocks
- `scripts/check.sh` läuft grün (oder du nennst genau, was nicht läuft und warum).
- Pull Request mit Zusammenfassung, Liste der Commits und der nicht getesteten Punkte.
- `docs/handover/ergebnis.md` ist für den Block ausgefüllt.
- Erst dann beginnt der nächste Block.
