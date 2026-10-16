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
