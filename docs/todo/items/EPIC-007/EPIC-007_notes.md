# EPIC-007 — Neuentwicklung als eigenständiges Tool

## 2026-10-16 — Architektur-Grundsatzfragen

### Discussed

- Ideensammlung in NOTE-002.
- IDs bei paralleler Arbeit in Cloud und lokal: Notes erhalten heute schon beim Import ein Label von der DB (Datei new-<name>.md), Backlog-Items noch nicht; die DB-Zeilen haben eine uid, die Markdown-Dateien nicht.
- Vorschlag Aufteilung: Core ohne Fachlichkeit, Plugins workspace (Projekte, Element-Register mit uid/Label, Verknüpfungen, Papierkorb), backlog, notes, später alarms.
- Vorschlag DB: Tabellen je Plugin mit eigener Migrationskette; Fremdschlüssel nur auf Plugins aus requires; fremde Daten sonst nur über Ports.

### Decided

- Markdown bleibt als Spiegel mit Sync, weil in der Cloud nur mit .md gearbeitet werden kann; der Sync muss später abschaltbar sein.
- Alles wird gespiegelt (Backlog, Notes, Topics, Verknüpfungen, später Wecker), soweit möglich; in der Cloud angelegte Einträge kommen in der DB an.
- Jeder Eintrag bekommt eine UUID, auch in der .md; das Label ist nur Anzeige. Ohne Label angelegte Einträge bekommen ihr Label beim Import, wie heute bei Notes.
- Prioritäten: 4 feste Werte Urgent, Important, Normal, Prospective (wie bisher), relational erzwungen, UI übersetzt; der Sync weist andere Werte ab.
- Stack bleibt Python/FastAPI und React/Vite/TypeScript, im Frontend Redux Toolkit.
- Frontend-Core wird aus ezf-ui kopiert, Login fliegt raus.
- Das Markdown-Format wird in diesem Projekt definiert; der Harness wird danach angepasst.
- Harter Schnitt beim Umstieg, kein Parallelbetrieb.
- Plugins kommen aus einer festen Liste; Backend und Frontend liegen getrennt.

### Open

- Freigabe der Aufteilung Core/Plugins und der DB-Aufteilung.
- Wecker: eigenes Plugin; braucht er eine aktive Benachrichtigung (dann ein Hintergrund-Timer, gegen die heutige Regel)?
- Abbildung von High/Medium/Low bei der Migration.
- Bleiben freie Zusatzfelder an Items (heute item_extra_fields)?

## 2026-10-16 — Wiederverwendbarkeit, Schema, Wecker, Prioritäten

### Discussed

- Vorschlag Wiederverwendbarkeit: Core und generische Bausteine (Element-Register, Baum, Verknüpfungen, Papierkorb, Sync-Engine, Markdown-Übersetzer-Rahmen, UI-Bausteine) so bauen, dass neue Plugins sie nur konfigurieren.

### Decided

- Größeres Augenmerk auf Wiederverwendbarkeit.
- Keine freien Zusatzfelder: das Schema ist fest; Neues kommt als Schemaänderung.
- Wecker benachrichtigt nur, solange der Viewer läuft.
- Migration der Altprioritäten: High → Urgent (Dringend), Medium → Important (Wichtig), Low → Normal.

### Open

- Wiederverwendbarkeit: innerhalb des Tools (Bausteine für Plugins) oder auch über Projekte hinweg (Core als eigenes Paket)?
- Wecker-Benachrichtigung im Frontend (Timer + Browser-Meldung) oder im Backend-Prozess?

## 2026-10-16 — Speicher, SSE, Wecker

### Discussed

- Sync: zwei Infrastrukturen (Datenbank, Dateien), die dieselben Speicher-Ports erfüllen; der Sync ist ein Dienst über beiden Ports. Plugin-spezifisch sind nur das Tabellen-Mapping (DB) und das Dateiformat (Dateien).
- Wecker im Backend: ein einzelner Timer auf den nächsten fälligen Zeitpunkt statt Polling; die Fällig-Entscheidung bleibt eine reine Funktion mit der Uhr als Parameter.

### Decided

- Wiederverwendbarkeit konsequent innerhalb des Projekts (Variante A); das Pluginsystem ist nur innerhalb dieses Projekts wiederverwendbar, kein eigenes Paket.
- Speicher: zwei Infrastrukturen, Datenbank und Dateien.
- Server-Sent Events als allgemeiner Kanal vom Backend ins Frontend (z. B. Sync-Updates); die API bleibt der Weg vom Frontend ins Backend.
- Der Wecker wird vom Backend ausgelöst und per SSE ans Frontend gemeldet; die UI hält keinen eigenen Zustand dafür.

### Open

- Regel 'kein Hintergrund-Timer' anpassen: Ausnahme für den Wecker-Timer im laufenden Backend.

## 2026-10-16 — Zerlegung in Stories und Tasks

### Discussed

- Der Projektinhaber wünscht den kompletten Umbau unter EPIC-007 zerlegt, mit Specs, damit die Umsetzung mit einem Go starten kann.
- Architekturentwurf als EPIC-007_spec.md; jedes Kind hat eine eigene Spec, die darauf verweist; Übersicht und Reihenfolge in Abschnitt 13.

### Decided

- Zerlegt in 2 Tasks und 25 Stories (TASK-034, TASK-035, STORY-060 bis STORY-084); alle Pflicht für das Epic.
- Offene Fragen sammelt STORY-060; jede Frage hat eine Annahme, die gilt, bis der Projektinhaber anders entscheidet.
- Specs enthalten Entscheidungen, Schnittstellen, Datenmodell und Akzeptanz, aber keine Schrittfolge (Harness-Regel); der Umsetzungsplan entsteht beim Start eines Items.
- Der Neubau entsteht in server/ und client/ neben dem Altcode, Port 5412, DB configs/viewer.db; Umstieg mit STORY-084.

### Open

- Freigabe der Architekturregeln (TASK-034) vor dem ersten Code.

## 2026-10-16 — Freigaben für die Umsetzung in der Cloud

### Discussed

- Der Projektinhaber lässt den Neubau über Nacht in einer Cloud-Sitzung umsetzen, ohne eingreifen zu können.

### Decided

- Umsetzungspläne brauchen keine Vorlage: Vor jedem Item steht der Plan in dessen Notizen, dann wird er umgesetzt. Abweichungen von der Spec kommen als Frage mit Annahme in STORY-060.
- Keine Releases, Versionen oder Tags bis zum Umstieg (1.0.0 mit STORY-084).
- Die Freigaben gelten auch für die Cloud-Sitzung; sie stehen in docs/handover/neubau-cloud.md.
- Der Altcode liegt in src_old/, die Vorlage des ezf-ui-Core in reference/ezf-ui/; beides ist nur Vorlage und wird erst nach Abnahme des Neubaus durch den Projektinhaber entfernt (neue Regel 0).
- Nicht in der Nacht: STORY-084 (Umstieg) und jeder Lauf gegen echte Daten (configs/todo.db); STORY-082 nur mit synthetischen Daten.

## 2026-10-17 — Stand nach der Cloud-Sitzung

### Discussed

- **Branch** `neubau/epic-007` (nie nach `main` gemergt, nie mit Gewalt gepusht). Der letzte Commit steht im Verlauf des Branches (`git log`, Titel „STORY-083: …“ bzw. der danach folgende Notiz-Commit). `scripts/check-next.sh` und `scripts/check.sh` waren bei jedem Commit der Items grün.
- **Je Item** (alle `Awaiting confirmation` mit allen Abschlusskriterien geprüft; Einzelheiten, Abweichungen und offene Punkte in den Notizen der Items unter „Umgesetzt und geprüft“, Annahmen als Fragen 13 bis 35 in `STORY-060`):
  - `STORY-061` bis `STORY-076`: Server-Grundgerüst, MCP-Host, Datenbank, Dateien, Sync, Client-Grundgerüst, gemeinsame Bausteine, workspace, Verknüpfungen, Papierkorb, Backlog (anzeigen, bearbeiten, Dokumente, Graph, Spiegel), Sync in der Oberfläche.
  - `STORY-077` Notes und Topics, `STORY-078` Auslöser, Hinweise, Befördern, Zurückstufen, `STORY-079` Notes im Spiegel: geprüft durch Unit-, Integrations- und Client-Tests samt Golden-Files; im Browser nur die Notes-Ansicht (Baum, Zähler, Detail) gesehen. Bekannt: ein Verweis zieht nach einem Typwechsel des Ziels erst beim nächsten Schreiben der Note nach; Datei und Datenbank derselben Note zugleich geändert ist ein Konflikt; „Befördern“ in der Fällig-Liste öffnet die Note statt des Dialogs; `\r\n` in Notes-Dateien ungetestet.
  - `STORY-080` Wecker: Server (genau ein Scheduler-Termin, Nachholen beim Start, Codec für `alarms.md`) und Client (Zähler, Banner, Benachrichtigung, `workspace.detail-sections`) getestet, dazu im Browser gesehen (Liste, Zähler, Detail-Abschnitt, Feuern durch den Scheduler). Nicht geprüft: echte Browser-Benachrichtigungen mit Berechtigung.
  - `STORY-081` KI-Schnittstelle: Gegenüberstellung aller Befehle von `backlog_api.py` und `notes_api.py` mit den Tools in `interfaces.md`; ergänzt wurden `core_health`, `backlog_index_lines`, `notes_index_lines`, `notes_move_note` (Projektwechsel) und das lesende `notes_get_notes_settings`; Systemtest `tests/implementation/system/server/test_harness_flow.py` (Ablauf über MCP gegen den ganzen Viewer). Nicht geprüft: ein echter MCP-Client des Harness.
  - `STORY-082` Datenübernahme: `python -m viewer.app.import_legacy` (`--legacy-db`, `--target`, `--dry-run`) mit synthetischer alter Datenbank (`tests/helpers/server/legacy_db.py`) getestet: Abbildungen, Prioritäten, Abbruchfälle, Dry-Run, zweiter Lauf = erster, Rundlauf im Viewer. **Nicht geprüft: jede echte Datenbank** (Regel der Sitzung), also auch ältere Schemastände des alten Viewers und der erste Sync danach (ohne Stand).
  - `STORY-083` Betrieb: Frontend-Auslieferung durch den Server, `server/Dockerfile`, Compose-Dienst `todo-viewer-next` (Port 5412), `todo.sh next …`, `operations.md`. Das Image wurde in der Sitzung gebaut und gestartet (mit CA-Zertifikat der Sitzung wegen eines TLS-abfangenden Proxys; Health, Frontend, `healthy`); der Image-Test selbst (`VIEWER_IMAGE_TEST=1`) lief hier nicht grün durch, aus demselben Grund. Dabei gefundener Fehler (fehlende `client/.npmrc` im Image) ist behoben. Nicht geprüft: `docker compose up` mit den echten Projekt-Ordnern, macOS.
- **Nicht umgesetzt:** `STORY-084` (Umstieg) — dem Projektinhaber vorbehalten. Kein Zugriff auf echte Daten (`configs/todo.db`, `configs/viewer.db`, Backups, andere Projekte); nichts in `src_old/` und `reference/` geändert.
- **Nicht in der Cloud geprüft:** ein Lauf des Neubaus gegen echte Daten, das Zeichnen des Abhängigkeiten-Graphen im Browser (React Flow braucht Layout; im Test ersetzt), große Projekte im Spiegel, die Leistung der Datenübernahme bei großen Datenbanken.

### Open

- Der Projektinhaber prüft die Items mit `Awaiting confirmation` und die Fragen 13 bis 35 in `STORY-060`; neu seit dem letzten Stand: Fragen 29 bis 35 (Notes, Wecker, Datenübernahme).
- Vor dem Umstieg (`STORY-084`): erst `import_legacy --dry-run` auf einer Kopie der echten Datenbank, Markdown-primäre Projekte vorher im alten Viewer in ihre Datenbank spiegeln, `server/constraints.txt` bei Abhängigkeits-Updates pflegen.
