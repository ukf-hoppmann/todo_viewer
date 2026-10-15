# Ergebnis der Cloud-Sitzung

Die Cloud-Sitzung füllt diese Datei je Block aus. Der Besitzer überträgt sie lokal ins Backlog (Status, Notes `Decided`) und entfernt sie danach. Nichts erfinden: „nicht getestet“ ist eine gültige Angabe.

## Vorlage je Block

### Block A / B / C — Stand

- Branch, Pull Request, letzter Commit:
- `scripts/check.sh`: Ergebnis im Wortlaut (grün, oder welcher Schritt scheitert):
- Plan des Blocks (Abschnitte mit Schnittstellen, kurz):

#### Item (z. B. TASK-031)

- Stand: fertig / teilweise / nicht begonnen
- Commits:
- Abweichungen von der Spec (mit Grund):
- Entscheidungen (kurz, als Liste für die Notes `Decided`):
- Neue Routen, Fehlercodes, Konfiguration, Migrationen (für die Doku):
- Offene Fragen an den Besitzer:
- Nicht getestet, und warum:

### Block A — Abgleich pro Eintrag (STORY-057: TASK-031, TASK-032, TASK-033)

- Branch, Pull Request, letzter Commit: `cloud/block-a-abgleich-pro-eintrag` (ab `cloud/abgleich-bloecke`); Pull Request und letzter Commit stehen im Abschlussbericht der Sitzung (PR #1).
- `scripts/check.sh`: grün (ruff, mypy `--strict`, import-linter 4 Verträge, pytest 1028 bestanden / 1 übersprungen, tsc, eslint, vitest 300 bestanden). Basislauf vor der ersten Änderung: ebenfalls grün (952 + 1 übersprungen, 301).
- Plan des Blocks (Abschnitte, einzeln testbar und integrierbar, Test zuerst; jeder Abschnitt hinterlässt einen grünen Stand):
  1. **TASK-031 Backup.** Schnittstellen: `domain/database_backup.py` (`backup_file_name(at, reason, attempt)`, `backups_to_remove(names, keep=10)`), Port `DatabaseBackup.create(reason) -> str | None`, Adapter `SqliteFileBackup` (`infrastructure/database/file_backup.py`), `Database(url, before_migration=…)` mit `migrations.has_pending`, `SyncService(..., db_backup=…)`, Fehler `DatabaseBackupFailedError` (`database_backup_failed`, 409).
  2. **TASK-032 Stand je Eintrag.** Schnittstellen: Migration 8 und Tabelle `sync_entries`; Port `SyncStateStore.load(project_id, folder) / save(project_id, folder, put, remove)`; Adapter `DatabaseSyncStateStore`; reine Funktionen in `domain/sync.py`: `classify_entry(database, markdown, stored) -> Change`, `plan_sync(...) -> SyncPlan` (Vorschau mit `origin`, `conflicts`, Token über beide Seiten und den Stand); `SyncStatus.conflicts`.
  3. **TASK-033 Entscheidungen.** Schnittstellen: `Resolution(kind, label, name, choice)`, `decide(plan, resolutions, direction) -> Decisions(transfers, deferred)`, `merged_items(own, other, take, drop)`; `SyncService.run(source, token, resolutions, direction, language, remember)`; API `resolutions`, Antwort `resolved/deleted/deferred/kept`.
  4. **Frontend-Anpassung (nur, damit der Block baut).** `SyncDialog` ohne „Fehlendes löschen“, mit Richtung „beide“ (Standard) und Liste der Konflikte; Entscheidungsdialog ist STORY-058 (Block B).
  5. **Integration.** `bootstrap.py` verdrahtet Backup und Stand; OpenAPI und `schema.d.ts` neu erzeugt; Technikdoku (`architecture`, `interfaces`, `operations`) und README.
- Stand der Items: TASK-031, TASK-032, TASK-033 und STORY-057 sind im Code fertig; die Abnahme „Migration an einer Kopie der echten Datenbank“ und „Probelauf legt die Datei an“ konnte die Cloud nicht prüfen (siehe unten).

#### TASK-031 — Automatisches Datenbank-Backup

- Stand: fertig (ohne Probelauf an der echten Datenbank).
- Commits: `TASK-031: Automatisches Datenbank-Backup vor Migration und Sync`.
- Abweichungen von der Spec: keine. Zu „Stoppen und fragen“: Die Migration läuft träge beim ersten Zugriff (`Database.begin`), der Backup-Ordner (`<CONFIG_DIR>/backups`) ist beim Bau des Containers aus den Settings bekannt, also läuft nichts vor dem Ordner. Ein fehlgeschlagenes Backup verhindert den Start **nicht** (es gibt keine Migration beim Start), sondern gibt 409 `database_backup_failed` bei der ersten Anfrage; die nächste Anfrage versucht es erneut. Das ist die Folge der trägen Migration, nicht der Vorschlag „Start bricht ab“; bitte bestätigen oder ein Prüfen beim Start anfordern.
- Entscheidungen:
  - Name `todo-JJJJMMTT-HHMMSS-<migration|sync>.db`, Wiederholung in derselben Sekunde `-2`, `-3` …; Aufbewahrung die letzten 10 dieser Muster (Sortierung nach Zeit und Zähler), alles andere im Ordner bleibt (auch `todo-…-vor-notes-sync.db`).
  - SQLite-Backup-Funktion in eine `.partial`-Datei, dort `journal_mode=DELETE`, `integrity_check` und Zeilenzahl je Tabelle, erst dann Umbenennen; Reste werden entfernt.
  - Backup vor Migration nur, wenn ein Schema mit Version 1 bis CURRENT−1 existiert (nicht bei neuer, leerer Datenbank, nicht bei aktuellem Schema); vor Sync nur, wenn der Lauf wirklich in die Datenbank schreibt.
  - Nur SQLite (`SqliteFileBackup.for_url` gibt für andere URLs `None`, dann gibt es kein Backup).
- Neue Fehlercodes: `database_backup_failed` (409, `details.reason`); Übersetzung `err.database_backup_failed` (de/en).
- Konfiguration/Migrationen: keine neue Einstellung; Ordner wie beim Wechsel der Primärquelle.
- Nicht getestet: Probelauf an einer Kopie von `configs/todo.db` (kein Zugriff); Verhalten bei einer sehr großen Datenbank (Dauer des Backups).

#### TASK-032 — Stand je Eintrag speichern

- Stand: fertig (ohne Migration an der Kopie der echten Datenbank).
- Commits: `TASK-032/033: Abgleich pro Eintrag mit Konflikten und Entscheidungen`.
- Abweichungen von der Spec:
  - Die Tabelle `sync_entries` hat zusätzlich die Schlüsselspalte `folder` (Markdown-Ordner, mit dem der Stand genommen wurde). Grund: ohne sie wäre der Stand nach einem Wechsel des Sync-Ordners falsch (Einträge würden gegen einen Stand eines anderen Ordners klassifiziert, ein Konflikt könnte als „nur eine Seite geändert“ und damit still überschrieben werden). Mit `folder` beginnt ein neuer Ordner ohne Stand (nur auf einer Seite = neu, auf beiden verschieden = Konflikt); beim Zurückwechseln gilt der alte Stand wieder.
  - Kein Fremdschlüssel auf `projects` (der Stand wird nur nach einem Lauf geschrieben; ein Projekt ohne Zeile gäbe sonst einen Fehler); Reste eines ausgetragenen Projekts bleiben harmlos liegen.
  - Die Vorschau hat keine Felder `missing`/`missing_documents` mehr (Löschungen sind Konflikte), dafür `origin` und `conflicts`.
- Entscheidungen:
  - Klassifikation `Change`: unverändert, Datenbank/Markdown geändert, beide geändert, Datenbank/Markdown neu, beide neu (verschieden), Datenbank/Markdown gelöscht, beide gelöscht (nur Reststand, wird vergessen). Konflikte: beide geändert, beide neu, gelöscht auf einer Seite (auch wenn die andere Seite sich nicht änderte).
  - Gleiche Seiten gelten als unverändert, wie sie dahin kamen; ihr Stand wird beim nächsten Lauf aufgefrischt (sonst würde eine spätere Änderung nur einer Seite als Konflikt erscheinen).
  - Dokumente eines Items, das nur auf einer Seite neu ist, reisen mit; die Dokumente eines Items, das nur auf einer Seite fehlt (Löschung), werden nicht einzeln gelistet, sie folgen der Entscheidung über das Item.
  - Der Stand wird am Ende des Laufs aus einem erneuten Lesen beider Seiten geschrieben (nur wo beide Seiten jetzt gleich sind), nicht aus der Absicht. Ein Abbruch mitten im Lauf kann so keinen falschen Stand hinterlassen.
  - Die Version von Items wird auf beiden Seiten gleich berechnet (`Item.version`; vorhandener Test Export → Import → Export gleiche Versionen); die Stop-Bedingung trat nicht ein.
  - Item-Reihenfolge: eine Seite behält ihre Reihenfolge, übernommene Einträge ersetzen an Ort und Stelle, neue folgen ihrem Vorgänger der anderen Seite (`merged_items`).
- Neue Routen/Felder: `GET /sources/{id}/sync-status` und `GET /sync-status` liefern zusätzlich `conflicts`; Migration 8.
- Offene Fragen: `state` bleibt `in_sync`, solange nur aufgeschobene Konflikte offen sind (der Gesamtstand zählt das nicht als Änderung); die UI muss `conflicts` zusätzlich zeigen (STORY-058/059). Soll `state` stattdessen etwas wie `conflicts` melden?
- Nicht getestet: Migration 8 an der Kopie der echten Datenbank; Laufzeit bei sehr vielen Einträgen (der Stand wird beim ersten Lauf für jeden Eintrag geschrieben, beim Status wird er für jede Anfrage geladen).

#### TASK-033 — Konflikte entscheiden

- Stand: fertig.
- Commits: `TASK-032/033: Abgleich pro Eintrag mit Konflikten und Entscheidungen`, `Web: Sync-Dialog an den Abgleich pro Eintrag angepasst`, `Doku: Abgleich pro Eintrag …`.
- Abweichungen von der Spec:
  - `delete_missing` entfällt ganz (der Vorschlag der Spec wurde übernommen): ein Aufruf damit ergibt 400 `bad_request`.
  - `kept` bedeutet jetzt: die aufgeschobenen Löschungen (Eintrag bleibt, wo er ist); `deferred` sind alle aufgeschobenen Konflikte.
  - Das Frontend wurde in Block A minimal angepasst (Spec „Nicht anfassen: UI“), weil sonst `tsc` und die Web-Tests des Blocks nicht laufen: `SyncDialog` zeigt Konflikte als Liste ohne Entscheidung (läuft also aufschiebend), die Richtung hat die Wahl „beide“ (Standard), „nur Datenbank → Ordner“, „nur Ordner → Datenbank“. Den Entscheidungsdialog liefert Block B.
- Entscheidungen:
  - `direction` fehlt = beide Richtungen; ein Markdown-Projekt ohne Datenbank-Spiegel läuft immer nur `from_md`. Ein fehlender Ordner ist eine leere Seite nur dort, wo nichts verloren geht (Ordner ist Ziel oder Spiegel); beim Lesen aus der Primärquelle bleibt es der Fehler `sync_source_invalid`/`not_found`.
  - Reihenfolge der Schreibzugriffe: erst die Datenbankseite (eine Transaktion, danach das Backup bereits gemacht), dann der Ordner; je Zielseite wie bisher (Ordner: Dokumente vor `TODO.md`; Datenbank: Backlog vor Dokumenten). Das passt weiter mit Entscheidungen je Eintrag; die Stop-Bedingung trat nicht ein.
  - Ein Dokument wird nur auf eine Seite geschrieben, wo das Item es führt (`Notes`/`Spec`); sonst bleibt es offen und taucht wieder auf.
  - Entscheidungen für unbekannte oder nicht (mehr) bestehende Konflikte werden ignoriert; eine Entscheidung, die eine durch `direction` ausgeschlossene Seite schreiben würde, bleibt aufgeschoben.
  - Das Token deckt beide Seiten und den gespeicherten Stand ab; die Entscheidungen gehören nicht dazu.
  - Löschen per Entscheidung: `database`/`markdown` = der Zustand dieser Seite gilt; fehlt der Eintrag auf ihr, wird er auf der anderen gelöscht (mit seinen Dokumenten), fehlt er auf der anderen, dort wiederhergestellt (mit Dokumenten).
  - Der Status-Hinweis an die Notes (`item_status_changed`) wird jetzt aus dem Vergleich der Primärquelle vor und nach dem Lauf abgeleitet (galt vorher nur bei Ziel = Primärquelle).
  - Der Export für das Backup beim Wechsel der Primärquelle schreibt keinen Stand (`remember=False`).
- Neue Routen, Fehlercodes, Konfiguration, Migrationen: `POST /sources/{id}/sync` mit `resolutions`, Antwort mit `conflicts`, `resolved`, `deferred` (statt `missing`, `delete_missing`); keine neue Route; Code `database_backup_failed`; Migration 8; OpenAPI und `schema.d.ts` neu erzeugt.
- Bekannte Grenzen: Wird ein Item per Entscheidung gelöscht, auf das andere Items verweisen, bricht die schreibende Seite mit `lifecycle_violation` (409) ab; die Datenbankseite wird zuerst und in einer Transaktion geschrieben, dann ist nichts geändert. Ein aufgeschobener Dokument-Konflikt kann verschwinden, wenn ein anderer Eintrag (das Item) per Lauf die Dokumentliste der Zielseite ändert; das Dokument selbst wird nie gelöscht.
- Nicht getestet: UI nur mit Komponententests, keine Sichtprüfung; Gleichzeitigkeit mehrerer Prozesse (Sperre gilt je Projekt im Prozess).

### Block B — Dialog und Auto-Sync (STORY-058, STORY-059)

- Branch, Pull Request, letzter Commit: `cloud/block-b-dialog-auto-sync` (ab `cloud/block-a-abgleich-pro-eintrag`); Pull Request und letzter Commit im Abschlussbericht der Sitzung (PR #2).
- `scripts/check.sh`: grün (ruff, mypy `--strict`, import-linter, pytest 1065 bestanden / 1 übersprungen, tsc, eslint, vitest 321 bestanden).
- Plan des Blocks:
  1. **STORY-058 Diff und Entscheidungen.** Reine Funktionen `domain/diff.ts` (`diffLines`, Zeilenvergleich per längster gemeinsamer Teilfolge, keine neue Abhängigkeit) und in `domain/sync.ts` `conflictKey`, `choiceOf`, `buildResolutions`, `changedFields`; Komponente `SyncConflicts` (Entscheidung je Konflikt, Vorbelegung Aufschieben, Vergleich); `SyncDialog` schickt `resolutions` mit der Bestätigung.
  2. **STORY-059a Schalter und Backup.** Migration 9 `projects.auto_sync`, `Source.auto_sync`/`auto_sync_active`, API-Feld `auto_sync` (Fehler `auto_sync_needs_mirror`), Backup-Grund `auto` (höchstens einmal pro Stunde, Aufbewahrung: letzte 10 plus das jüngste je Tag der letzten 14 Tage).
  3. **STORY-059b strenger Lesemodus.** Port `MergeMarkerCheck`, Adapter `MarkdownMergeMarkers`; `SyncService.preview/run(auto=True)`: fehlender Ordner und Merge-Marker sind `sync_source_invalid` (`merge_markers`).
  4. **STORY-059c Dienst und Timer.** `AutoSyncService.tick/info/ensure_running/stop` (feste Uhr in den Tests, kein echter Timer außer in einem Test mit 10 ms), Verdrahtung in `bootstrap.py`, Lebenszyklus in `create_app`, Status-Felder `auto_*`.
  5. **Frontend und Integration.** Schalter, Lauf-/Pausen-/Konfliktanzeige in der Projektkarte, ⚠ in der Sidebar bei Konflikten; Doku (`architecture`, `interfaces`, `operations`, `configuration`, README).

#### STORY-058 — Konflikte mit Diff-Ansicht

- Stand: fertig (Komponententests, keine Sichtprüfung).
- Commits: `STORY-058: Konflikte im Sync-Dialog mit Diff-Ansicht entscheiden`.
- Abweichungen von der Spec: keine. „Beleg per Screenshot (`preview_start`)“ ist nicht möglich (Cloud) und bleibt dir.
- Entscheidungen:
  - Eigene Zeilenvergleichsfunktion statt neuer Bibliothek (die Spec-Frage „Bibliothek oder eigene Funktion“ ist damit beantwortet; keine neue npm-Abhängigkeit).
  - Items: Tabelle der unterschiedlichen Felder nebeneinander (Datenbank | Datei); Felder mit Zeilenumbruch oder über 60 Zeichen als Zeilenvergleich (− nur Datenbank, + nur Datei); Dokumente als Zeilenvergleich; fehlt eine Seite, steht das dabei.
  - Entscheidung je Konflikt als Radiogruppe „Aufschieben“ (vorbelegt), „Datenbank gilt“, „Datei gilt“; Entscheidungen leben im Zustand des Dialogs und gehen mit der Bestätigung (nur nicht aufgeschobene).
  - Beim Umstellen der Primärquelle werden keine Entscheidungen geschickt; die Konflikte müssen vorher in einem normalen Sync entschieden sein (Schaltfläche gesperrt).
- Neue Routen/Codes: keine.
- Nicht getestet: Aussehen (CSS für `.sync-conflicts`, `.diff-*`), große Texte.

#### STORY-059 — Auto-Sync

- Stand: fertig (ohne Probelauf mit echtem Git-Pull und ohne Sichtprüfung).
- Commits: `STORY-059: Schalter für den Auto-Sync je Projekt, Backup-Aufbewahrung nach Alter`, `STORY-059: Auto-Sync-Dienst mit Beruhigungszeit, Merge-Marker-Schutz und Timer`, `STORY-059 Web: …`, `Doku: …`.
- Abweichungen von der Spec: keine; die Vorschläge der Spec wurden übernommen (Intervall 30 s, Beruhigungszeit, Merge-Marker, Backup höchstens einmal pro Stunde, Aufbewahrung 10 plus je Tag 14 Tage).
- Entscheidungen (für die Notes `Decided`):
  - Intervall: Umgebungsvariable `AUTO_SYNC_INTERVAL` (Sekunden, Standard 30, `0` = kein Timer); nicht einstellbar in der UI, die Beruhigungszeit ist fest „zwei gleiche Prüfungen“ (= ein Intervall).
  - Beruhigung über das Token der Vorschau: Es deckt beide Seiten und den Syncstand ab, ein laufender Pull ändert es.
  - Der erste Lauf nach dem Start prüft nur und merkt sich den Stand; übernommen wird bei der zweiten Prüfung. Ein Lauf „beim Start“ gibt es als erste Prüfung.
  - Der Timer ist ein Thread (`daemon`), der beim Start der App (Lebenszyklus von FastAPI) und beim Einschalten des Schalters per API startet und sich beendet, sobald kein Projekt den Schalter hat. Der Schalter wirkt nur mit Spiegel (`auto_sync_active`).
  - Auto-Läufe lesen streng: fehlender Ordner, nicht lesbare Dateien und Merge-Marker pausieren das Projekt (`auto_paused`); ein Merge-Marker braucht eine Startzeile `<<<<<<<` und eine Endzeile `>>>>>>>` (eine `=======`-Unterstreichung allein ist keiner).
  - Der letzte Lauf und die Pause liegen nur im Speicher (nach einem Neustart leer).
  - Auto-Läufe benutzen `SyncStatusService.run`, zeichnen also den Stand wie jeder Sync auf, und dieselbe Sperre je Projekt.
  - Die Sidebar markiert ein Projekt mit offenen Konflikten (⚠, Tooltip „N offene Konflikte“), auch wenn `state` `in_sync` sagt.
- Neue Routen, Fehlercodes, Konfiguration, Migrationen: `PUT/POST /sources` mit `auto_sync`; `SourceOut.auto_sync`; `GET /sync-status` mit `auto_sync`, `auto_last_run_at`, `auto_paused`; Fehler `auto_sync_needs_mirror` (400); `err.merge_markers` (Übersetzung); Umgebungsvariable `AUTO_SYNC_INTERVAL`; Migration 9; Backup-Grund `auto`.
- Offene Fragen an den Besitzer:
  - Der Sync-Status in der UI wird nur beim Laden, Fokus und von Hand geholt (Regel der Web-Architektur): Ein Lauf des Auto-Syncs erscheint in der UI also erst nach dem nächsten Fokus/Neuladen oder „Status prüfen“. Soll die UI (wie die Fälligkeitsanzeige) minütlich nachfragen, solange irgendein Projekt Auto-Sync hat? Das wäre eine Änderung der Web-Regel (§3 Zustand) und ist hier nicht gebaut.
  - Die Notes (STORY-047) nimmt der Auto-Sync erst mit Block C mit.
- Nicht getestet: echter Git-Pull in einem Mehrprozess-Betrieb; Laufzeit der Prüfung bei großen Backlogs (jede Prüfung liest beide Seiten wie `GET /sync-status`, gemessen: nicht); Verhalten im Docker-Betrieb (Timer-Thread beim Herunterfahren: `stop()` wartet höchstens 5 s).

### Was der Besitzer lokal noch tun muss

- (z. B. Migration an einer Kopie der echten Datenbank prüfen, Backup, `./todo.sh update`, UI-Sichtprüfung, Backlog-Status setzen)
