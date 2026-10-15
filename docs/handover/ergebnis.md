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

- Branch, Pull Request, letzter Commit: `cloud/block-b-dialog-auto-sync` (ab `cloud/block-a-abgleich-pro-eintrag`); Pull Request: #2, Basis `cloud/block-a-abgleich-pro-eintrag`.
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
  - Entschieden (Besitzer): Die UI fragt den Sync-Status jede Minute ab, solange ein Projekt Auto-Sync hat (nicht bei pausiertem Polling), und lädt die Items neu, wenn ein neuer Auto-Lauf gemeldet wird; gebaut in Block C (`useSyncStatuses`, `useReloadOnAutoSync`). Manuell: „Status prüfen“ in der Projektkarte und der Sync-Dialog (Vorschau, Ausführen) funktionieren jederzeit, auch nach einem Pull.
  - Die Notes (STORY-047) nimmt der Auto-Sync seit Block C mit (derselbe Sync); eine Note ohne Label im Ordner wird dann auch automatisch importiert und ihre Datei umbenannt.
- Nicht getestet: echter Git-Pull in einem Mehrprozess-Betrieb; Laufzeit der Prüfung bei großen Backlogs (jede Prüfung liest beide Seiten wie `GET /sync-status`, gemessen: nicht); Verhalten im Docker-Betrieb (Timer-Thread beim Herunterfahren: `stop()` wartet höchstens 5 s).

### Block C — Notes im gemeinsamen Sync (STORY-047: TASK-024 bis TASK-027)

- Branch, Pull Request, letzter Commit: `cloud/block-c-notes-im-sync` (ab `cloud/block-b-dialog-auto-sync`); Pull Request: #3, Basis `cloud/block-b-dialog-auto-sync`.
- `scripts/check.sh`: grün (ruff, mypy `--strict`, import-linter 4 Verträge, pytest 1173 bestanden / 1 übersprungen, tsc, eslint, vitest 329 bestanden).
- Plan des Blocks:
  1. **TASK-024 Format.** `domain/notes_markdown.py` (reine Funktionen): `render_note`/`render_parsed`/`parse_note`, `render_topics`/`parse_topics`, `render_counters`/`parse_counters`, `NoteFormatError` (`note_format`, Zeilennummer); Golden-Files `backend/tests/golden/notes/`.
  2. **TASK-025 Datei-Adapter.** Port `NotesMirror` (`read`, `write(expected)`, `delete`, `fingerprint`, `files_with_markers`), Adapter `infrastructure/notes_files/FilesNotesMirror` (atomar, `mirror_conflict`, Zeilenenden bleiben), Import-Linter-Vertrag „unabhängig von markdown und database“.
  3. **TASK-026 Sync.** `NoteRepository.store_topic/store_note/counters/raise_counter/next_label` (Migration nicht nötig), `domain/notes_sync.py` (Einträge, Versionen, Label-Regeln), `plan_sync(extras=…)` mit `ExtraEntry` und den Abschnitten `topics/notes/note_documents`, `NotesSync` (Lesen und Anwenden), Einbindung in `SyncService`, Status und Fingerabdrücke; API-Abschnitte; Doku des Formats.
  4. **TASK-027 Oberfläche.** `domain/sync.ts` (`SYNC_KINDS`, `visibleKinds`, `summarizePreview`, Zählung inkl. Notes), `SyncDialog` mit den Abschnitten, `SyncConflicts` stellt `note`, `topic` und `note_document` dar, Fehlertexte.
  5. **Integration.** `bootstrap.py`, OpenAPI und `schema.d.ts`, Technikdoku (`interfaces`, `architecture`, `operations`), README.

#### TASK-024 — Dateiformat

- Stand: fertig.
- Commits: `TASK-024: Dateiformat für Notes, Topics und Zähler (domain/notes_markdown.py)`.
- Abweichungen von der Spec: Das Format folgt der Spec. Ergänzt wurde, was sie offen ließ: Zeitpunkte mit Bruchteilen von Sekunden (`…:00.5Z`) nur wo vorhanden, damit nichts verloren geht; `Topic: new:<Name>` und `note:new-<kurzname>` wie festgelegt; die Kopfzeilen `Summary` bis `Deleted` stehen immer (leer, wenn ohne Wert), `Triggers:`/`Links:` nur wenn es Einträge gibt; ein leerer Langtext und `None` sind dasselbe.
- Entscheidungen:
  - Ein Event-Auslöser nennt das Ziel als `Projekt:Label` (Projektnamen mit Leerzeichen sind erlaubt) und den Status am Zeilenende (`Completed`, `In progress`, …).
  - Ein Link-Ziel `topic:`/`note:` ist nicht von einem Projekt dieses Namens zu unterscheiden (bekannte Grenze, in der Doku genannt).
  - Dateiname und Label müssen übereinstimmen (`NOTE-001.md` enthält `# NOTE-001`); eine Note ohne Label liegt in `new-<kurzname>.md`.
- Nicht getestet: der Harness (Dateimodus) gegen das Format (außerhalb der Cloud).

#### TASK-025 — Datei-Adapter

- Stand: fertig.
- Commits: `TASK-025: Datei-Adapter für den Notes-Spiegel (infrastructure/notes_files)`.
- Abweichungen von der Spec: Der Port ist **dateiweise** (`read(source) -> {Name: Text}`, `write(source, name, text, expected)`, `delete`, `fingerprint`, `files_with_markers`) statt `write(source, snapshot, expected_fingerprint)`. Grund: Format und Regeln gehören nach `domain`, der Adapter bleibt ohne Notes-Logik; der Konflikt wird je Datei geprüft (`expected` = Inhaltsversion der gelesenen Datei).
- Entscheidungen: erlaubt sind nur die Dateinamen des Formats (alles andere im Ordner wird weder gelesen noch angefasst); der Spiegel-Ordner ist `<Markdown-Ordner>/notes/` (auch bei Projekten mit Markdown als Primärquelle); temporäre Datei im selben Ordner plus `os.replace`.
- Neue Fehlercodes: `mirror_conflict` (409), Übersetzung `err.mirror_conflict`.
- Nicht getestet: Dateisystem ohne atomares Umbenennen (Netzlaufwerke).

#### TASK-026 — Notes im gemeinsamen Sync

- Stand: fertig.
- Commits: `TASK-026 (1/3): Datenbank-Import …`, `TASK-026: Notes, Topics und Note-Dokumente im gemeinsamen Sync`.
- Abweichungen von der Spec:
  - Zähler: `counters.md` ist kein Vergleichseintrag; sie wird geschrieben, wenn ein Lauf Notes in den Ordner schreibt (und die Zähler sich unterscheiden), und beim Import zählt sie als Untergrenze. Ein Projekt, dessen einziger Unterschied die Zähler sind, gilt als gleich.
  - Der Import ist nicht eine einzige Datenbank-Transaktion (mehrere Aufrufe am `NoteRepository`); Konsistenz kommt aus dem Stand je Eintrag, der nur für wirklich gleiche Einträge geschrieben wird.
  - Der Gesamt-Fingerabdruck umfasst die Notes nur, wenn es welche gibt: Projekte ohne Notes behalten ihre Baseline; Projekte mit Notes gelten einmalig als geändert (`primary_changed`/`mirror_changed`), bis zum nächsten Sync (wie in der Spec vorhergesagt; die Stop-Bedingung „mehr als der einmalige Wechsel“ trat nicht ein).
- Entscheidungen (für die Notes `Decided`):
  - Neue Eintragsarten `topic`, `note`, `note_document` im selben Stand je Eintrag; Dokumente einer neuen Note reisen mit, die einer auf einer Seite fehlenden Note folgen der Entscheidung über die Note.
  - Label-lose Einträge (`new-…`, `NEW`) sind immer „im Ordner neu“; die Labels vergibt die Datenbank in der Reihenfolge der Datei (Topics) bzw. nach Name (Notes); im selben Lauf wird die Datei in `NOTE-xxx.md` umbenannt (samt Dokumenten, Verweisen und `topics.md`). Bei `direction: from_md` werden sie nicht übernommen (es dürfte sonst der Ordner nicht geschrieben werden und der Eintrag würde beim nächsten Lauf doppelt importiert).
  - Ein Topic als Elternknoten, der in der Datenbank fehlt, ergibt beim Import ein Topic ohne Eltern; eine Note unter einem unbekannten Topic wird ohne Topic übernommen (der Import scheitert nicht an Regeln).
  - Eine Note oder ein Topic per Entscheidung löschen = endgültig entfernen (`purge`), mit Dokumenten und Links; Kinder und Notes eines gelöschten Topics verlieren den Verweis.
  - Format-Fehler brechen den Sync vor jeder Änderung ab (`sync_source_invalid`, `reason=note_format`).
  - Die Notes laufen im selben Backup-Schritt: jeder Lauf, der in die Datenbank schreibt, sichert vorher (auch Notes).
- Neue Routen, Fehlercodes, Konfiguration, Migrationen: Antwort von `POST /sources/{id}/sync` mit `topics`, `notes`, `note_documents`; `resolutions[].kind` und `conflicts[].kind` um `topic`, `note`, `note_document`; keine neue Migration (die Tabellen von Version 6 reichen); keine neue Einstellung.
- Offene Fragen an den Besitzer: (1) Soll `counters.md` auch dann geschrieben werden, wenn sonst nichts zu übertragen ist? (2) Ein Projektname `topic` oder `note` ist als Link-Ziel mehrdeutig (Format-Grenze). (3) Auto-Sync mit Notes importiert Notes ohne Label und benennt Dateien um, ohne zu fragen; soll das nur manuell geschehen?
- Nicht getestet: ein echter Cloud-Lauf (claude.ai) mit Git; sehr viele Notes (Lesen beider Seiten bei jeder Prüfung, jeder Auto-Lauf liest alle Notes mit Links, Auslösern und Dokumenten); Gleichzeitigkeit zwischen Viewer und Datei-Editor während eines Laufs über den Test mit `mirror_conflict` hinaus.

#### TASK-027 — Notes in der Oberfläche

- Stand: fertig (Komponententests, keine Sichtprüfung).
- Commits: `TASK-027: Notes im Sync-Dialog` (und Doku).
- Abweichungen von der Spec: keine. Das Statussymbol braucht keinen neuen Code (Status und Fingerabdrücke sind gemeinsam; getestet über die API: eine extern geänderte Notes-Datei ergibt `mirror_changed`).
- Entscheidungen: Abschnitte für Topics, Notes und Notes-Dokumente erscheinen nur, wenn etwas drin ist; Note-Konflikte werden feldweise dargestellt, der Langtext (`body`) als Zeilenvergleich, Dokumente der Notes wie Dokumente; Fehlertext für `note_format` nennt Datei und Zeile.
- Nicht getestet: Screenshot und manueller Durchlauf „Export und Import einer Note, Notes-Konflikt entscheiden“ (siehe unten).

### Was der Besitzer lokal noch tun muss

Reihenfolge der Pull Requests: A (`cloud/block-a-abgleich-pro-eintrag`, PR #1) → B (PR #2) → C. Jeder PR zeigt auf den vorigen Branch; erst A in `cloud/abgleich-bloecke`, dann B, dann C mergen (oder den Stapel in einem Zug), danach `cloud/abgleich-bloecke` nach `main`.

1. **Vor dem Deployment ein Backup** der echten Datenbank (Vorgabe): ab Block A legt der Viewer vor jeder Migration und jedem Sync in die Datenbank selbst eines an (`configs/backups/todo-<Zeit>-<migration|sync|auto>.db`); das erste Mal also vor dem ersten Start mit der neuen Version prüfen, dass der Ordner beschreibbar ist.
2. **Migrationen 8 (Stand je Eintrag) und 9 (Auto-Sync-Schalter) an einer Kopie von `configs/todo.db` prüfen** (Daten unverändert, Zeilenzahlen gleich) und erst dann `./todo.sh update`. In der Cloud nicht möglich.
3. **Probelauf des Backups** an der Kopie: erwartete Datei in `configs/backups/` und `integrity_check`.
4. **Einmaliger Statuswechsel:** Projekte mit Spiegel und Notes gelten nach dem Update einmalig als geändert, bis zum nächsten Sync; danach in Ordnung. Wer will, schaut sich beim ersten Sync die Vorschau genau an: ohne gespeicherten Stand gilt „auf beiden Seiten vorhanden und verschieden“ als Konflikt (Aufschieben ist vorbelegt).
5. **UI-Sichtprüfung mit Screenshot** (nicht in der Cloud): Sync-Dialog mit Konflikten (Item, Dokument, Note, Topic, Löschung) und allen drei Entscheidungen; Projektkarte mit Auto-Sync-Schalter, letztem Lauf, Pause und Konfliktzahl; Sidebar-Symbol bei Konflikten.
6. **Auto-Sync ausprobieren:** Schalter an einem Projekt einschalten, Datei per `git pull` ändern, nach zwei Prüfungen (Standard 60 s) ist die Änderung in der Datenbank; Merge-Marker in einer Datei erzeugen (Projekt pausiert); Schalter aus. Intervall über `AUTO_SYNC_INTERVAL` (Sekunden, `0` = kein Timer; im Docker-Betrieb in `docker-compose.yml` ergänzen, wenn ein anderer Wert gewünscht ist).
7. **Backlog nachtragen** (die Cloud hat `docs/todo/**` bewusst nicht angefasst): Status der Items STORY-057, TASK-031 bis TASK-033, STORY-058, STORY-059, STORY-047, TASK-024 bis TASK-027 setzen (`Awaiting confirmation`), die Entscheidungen aus den Abschnitten oben in die Notes (`Decided`) übernehmen, die offenen Fragen beantworten. Die Spiegel-Dateien dieser Doku (`docs/todo`) danach mit dem Sync neu abgleichen.
8. **Tagesbericht und SemVer-Release** (nicht in der Cloud): Der Release ändert Verhalten und Schnittstellen (neue Sync-API, `delete_missing` entfällt, neue Migrationen 8 und 9) und ist damit mindestens ein Minor-Schritt, wegen des entfernten Felds `delete_missing` und der geänderten Antwort von `POST /sources/{id}/sync` für Aufrufer der API ein Bruch.
9. **Harness (Dateimodus)** gegen das Notes-Format in `docs/techdocs/interfaces.md` bauen bzw. prüfen.
10. **Aufräumen:** `docs/handover/cloud-sync.md` und diese Datei entfernen.
