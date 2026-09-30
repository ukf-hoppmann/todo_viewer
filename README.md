# ToDo Viewer

Lokale Web-UI zum Visualisieren von `TODO.md`-Backlogs im "backlog format version 2"
bzw. Claude_Harness-Backlog-Format. Jeder Eintrag braucht eine ID; einfache
Markdown-Checklisten werden nicht unterstützt.

## Quickstart (Docker)

```bash
./todo.sh start
```

Baut das Image (falls nötig), startet den Container im Hintergrund und öffnet
[http://todo.localhost:5411](http://todo.localhost:5411) (`*.localhost` wird
von macOS automatisch auf `127.0.0.1` aufgelöst, kein `/etc/hosts`-Eintrag
nötig). Der Container läuft mit `restart: unless-stopped` dauerhaft im
Hintergrund weiter — kein offenes Terminal nötig.

Weitere Befehle:

```bash
./todo.sh stop      # Container anhalten
./todo.sh restart   # Container neu starten
./todo.sh down      # Container + Netzwerk entfernen (configs/ bleibt erhalten)
./todo.sh update    # nach Code-Änderungen neu bauen (--no-cache) und ersetzen
./todo.sh logs      # Live-Log (logs/todo-viewer.log)
./todo.sh status    # läuft der Container?
./todo.sh open      # nur den Browser öffnen
```

## Quellen konfigurieren

Eine Quelle ist ein **Backlog-Ordner**, der eine `TODO.md` enthält
(Claude_Harness backlog format: `TODO.md`, `archive.md`, `items/<ID>/`).
`archive.md` im selben Ordner wird automatisch mitgelesen.

Projekte lassen sich direkt in der UI verwalten: **＋ Hinzufügen** neben
„Projekte“ öffnet einen Ordner-Browser (Startordner über `BROWSE_START`, im
Container `/Users/hoppmann/Documents/GitHub`); Ordner mit `TODO.md` sind
markiert. Über ✎/✕ hinter einem Projekt wird der Ordner geändert bzw. der
Eintrag entfernt. Ordner, die nicht (mehr) lesbar sind, bleiben ausgegraut mit
⚠ und Fehlermeldung in der Liste stehen. Ohne Projektname wird der Name des
umgebenden Git-Repos verwendet.

Die Projektliste liegt in der zentralen Datenbank `configs/todo.db`. Beim
Hinzufügen wählst du den Speicherort: ein **Markdown-Ordner** oder die
**Datenbank** (Name Pflicht, ein Sync-Ordner ist optional). Datenbank-Projekte
tragen in der Liste das Kürzel „DB“. Ist ein Sync-Ordner eingetragen, öffnet ⇄
den Abgleich mit dem Ordner: erst eine **Vorschau** (neu, geändert,
unverändert; was nur auf dem Ziel liegt, steht als Warnung dabei und bleibt
stehen, es sei denn, du löschst es), dann **Ausführen**. Im Bearbeiten-Dialog
stellt „In die Datenbank übernehmen…“ bzw. „Als Markdown-Ordner ablegen…“ das
Projekt um: Der Dialog synchronisiert, danach liegt das Projekt am anderen Ort;
die Item-IDs bleiben gleich, die Markdown-Dateien bleiben liegen. Dieselben
Schritte gibt es über die API (`/api/v2/sources`, `/sources/{id}/sync`).
Projekte, die frühere Versionen in
`configs/config.json` eingetragen hatten, werden beim ersten Start übernommen
(Sicherung `config.json.bak`, siehe [Konfiguration](docs/techdocs/configuration.md)).

Änderungen an den Backlog-Dateien werden automatisch
übernommen — das Frontend pollt `/api/v2/backlog` alle 5 Sekunden neu
(pausiert, solange ein Dialog offen ist oder ein Feld bearbeitet wird).

Der `configs/`-Ordner ist per Volume in den Container gemountet und liegt
physisch auf dem Host — er übersteht `./todo.sh down` und Rebuilds. Dort
liegen `config.json` und die Datenbank `todo.db` mit Projektliste und
UI-Zustand (ausgeblendete Filterwerte, eingeklappte Knoten, markierte
Projekte, Ansicht, Auswahl, Sprache).

## Bearbeiten

Status, Priorität, Bereich, „Pflicht für Parent“ und Abhängigkeiten lassen
sich direkt im Detail-Panel ändern; jede Änderung wird sofort gespeichert.
Der Bereich wird aus den Bereichen desselben Backlogs gewählt, „＋ Neuer
Bereich…“ legt einen neuen an (Enter speichert, Esc bricht ab). Schlägt eine
Änderung fehl, etwa weil der Eintrag inzwischen geändert wurde, steht die
Meldung am Feld und es gilt wieder der Stand der Datei.
Alles andere ändert der Bearbeiten-Modus: „✎ Bearbeiten“ öffnet ein Formular
für Titel, Status, Priorität, Bereich, Parent (mit „Pflicht für Parent“),
Abhängigkeiten, Ziel, Fertigstellungskriterien und Kurzfassung. Erst
„Speichern“ schreibt alle Änderungen in einem Schritt, „Abbrechen“ verwirft
sie. Wird ein Eintrag auf `Completed` oder `Rejected` gesetzt, fragt das
Formular bzw. ein Dialog nach einer `Resolution` und der Eintrag wandert nach
`archive.md`; ein Zurücksetzen auf einen offenen Status holt ihn (ohne
Resolution) zurück nach `TODO.md`.
Notizen und Specs lassen sich im Dokument-Dialog schreiben: „📝 ＋ Notiz-Eintrag“
hängt einen datierten Eintrag (Thema, Besprochen, Entschieden, Offen) an,
„✎ Bearbeiten“ ändert den ganzen Text einer Notiz oder Spec mit
Markdown-Vorschau, „📐 ＋ Spec anlegen“ legt eine neue Spec an. Hat jemand das
Dokument inzwischen geändert, bleibt der eigene Text stehen; „Aktuellen Stand
anzeigen“ zeigt die fremde Fassung, erst „Trotzdem speichern“ überschreibt sie.
„🗑 Löschen“ im Detail-Panel verschiebt einen Eintrag in den Papierkorb. Hat
er Kinder, nennt der Dialog sie zuerst und löscht sie erst nach einer zweiten
Bestätigung mit.
„🔁 Typ ändern“ wandelt einen Eintrag in einen anderen Typ um. Weil der Typ das
Präfix der ID ist, bekommt er die nächste freie ID des neuen Typs; Parent,
Abhängigkeiten, Notizen und Specs im Backlog ziehen mit, und der Eintrag ist
danach unter der neuen ID ausgewählt. Ein Hinweis nennt alte und neue ID und
dass Verweise außerhalb des Backlogs (Techdocs, Berichte, Code) die alte ID noch
enthalten können; er bleibt stehen, bis man ihn schließt.
Neue Einträge legt „＋ Neu“ in der Leiste über den Ansichten an (ohne
Parent, Projekt wählbar); „＋ Kind anlegen“ im Detail-Panel eines Epics oder
einer Story legt ein Kind mit passendem Typ an und übernimmt den Bereich. Die
ID vergibt der Server; das neue Item wird danach ausgewählt.
Hat jemand den Eintrag inzwischen geändert, bleiben die Eingaben erhalten;
„Aktuellen Stand laden“ übernimmt die fremden Änderungen an nicht bearbeiteten
Feldern, danach kann erneut gespeichert werden. `Notes` und `Spec`
eines Eintrags öffnen sich in einem großen Dokument-Dialog.

Änderungen, die gegen die Parent-Regeln des Backlog-Formats verstoßen, lehnt
der Server mit einem Hinweis auf die blockierenden Einträge ab, z. B. ein
Parent auf `Completed`, solange ein Kind noch aktiv ist. Wird ein Eintrag
unter einem abgeschlossenen Parent angelegt, fragt der Dialog, ob der Parent
(und ggf. dessen geschlossene Vorfahren) wieder geöffnet werden soll, und legt
den Eintrag danach an.

Geschrieben wird atomar (temporäre Datei + Umbenennen), Zeilenenden (LF/CRLF)
bleiben erhalten. Hat jemand anderes (z. B. ein Agent) denselben Eintrag
inzwischen geändert, bricht das Speichern mit einem Hinweis ab, statt dessen
Änderung zu überschreiben; Änderungen an anderen Einträgen derselben Datei
stören nicht.

## Nutzung durch Agenten

Agenten pflegen Backlogs über die API unter `http://localhost:5411/api/v2`
statt die Dateien direkt zu bearbeiten: neuen Backlog anlegen
(`POST /backlogs` erzeugt `TODO.md`, `archive.md` und `items/` und trägt die
Quelle ein), Überblick, Anlegen, Ändern (mit
Versions-Token), Typ ändern (neue ID, Verweise folgen), Notizen und Specs, Löschen über einen Papierkorb
(wiederherstellen oder endgültig löschen, jeweils samt Kindern). Der Server prüft dabei die Regeln
des Backlog-Formats. Ablauf und Endpunkte: [Schnittstellen](docs/techdocs/interfaces.md#nutzung-durch-agenten).
Der Port ist nur lokal erreichbar.

## Sprache

Status, Prioritäten, Typen und Feldnamen sind in den Dateien englisch und
bleiben es. Der DE/EN-Schalter oben in der Sidebar übersetzt nur die Anzeige
(inkl. der gesamten Oberfläche); gefiltert und gespeichert wird immer mit den
englischen Werten. Alte deutsche Prioritäten (`Dringend`, `Wichtig`,
`Perspektivisch`) werden beim Lesen auf `Urgent`, `Important`, `Prospective`
abgebildet.

## Views

- **Baum**: Epic → Story → Task Hierarchie pro Projekt, mit Fortschrittsbalken.
  Items mit Kindern zeigen direkt hinter dem Titel einen Fortschrittskreis
  (Tortendiagramm) mit „erledigt/gesamt“ über alle Nachkommen; Kanban-Karten
  und Graph-Knoten zeigen ihn ebenfalls.
  „Epics zuklappen/aufklappen“ und „Stories zuklappen/aufklappen“ über dem Baum
  klappen alle Epics bzw. Stories auf einmal zu oder auf, auch ausgefilterte.
  Sie wirken auf die in der Seitenleiste markierten Projekte (Klick auf den
  Projektnamen markiert bzw. hebt die Markierung auf, mehrere möglich), ohne
  Markierung auf alle Projekte. Die Markierung wird mit dem UI-Zustand
  gespeichert; die Checkbox blendet ein Projekt weiterhin nur ein oder aus.
  Optionale Kinder (`Required for parent: No`) sind gestrichelt angebunden,
  gedimmt und haben einen hohlen Status-Punkt; sie zählen nicht zum Fortschritt.
  Abgelehnte Items (`Rejected`) zählen ebenfalls nicht mit.
- **Abhängigkeiten**: Gerichteter Graph aus dem `Dependencies`-Feld (zeigt nur
  Tasks mit tatsächlichen Abhängigkeiten, isolierte Tasks werden ausgeblendet).
  Das Layout (ELK, von links nach rechts) hält Kantenkreuzungen gering; alle
  Knoten ohne Abhängigkeiten stehen in der linken Spalte, unabhängige Teilgraphen
  untereinander. Der ausgewählte, der überfahrene und alle zusätzlich markierten
  Knoten werden mit ihren Kanten und direkten Nachbarn hervorgehoben, der Rest
  wird abgeblendet. Klick wählt aus bzw. wieder ab, ⌘-/Strg-/⇧-Klick markiert
  weitere Knoten, Esc oder ein Klick ins Leere setzt alles zurück.
- **Kanban**: Spalten nach Status (Open, In progress, Awaiting confirmation,
  Completed, Rejected).
- **Papierkorb**: Gelöschte Items aller Projekte mit Löschdatum.
  „Wiederherstellen“ holt ein Item samt Kindern zurück, „Endgültig löschen“
  entfernt es nach einer Bestätigung samt Kindern, Notizen und Specs.

Klick auf ein Item öffnet das Detail-Panel rechts mit allen geparsten Feldern
(inkl. aller Freitext-Felder wie `Implementation`, `Verification`, `Context` etc.).
Unter „Untergeordnet“ trägt jedes direkte Kind Rahmen und Punkt in der Farbe
seines Status (Tooltip: Titel und Status); Kinder im Papierkorb stehen
gestrichelt und durchgestrichen am Ende (Tooltip: Löschdatum).

## Architektur

Onion-Architektur im Backend: Abhängigkeiten zeigen nur nach innen, geprüft
per `import-linter`.

```
backend/todo_viewer/
  domain/          Item, Source, Backlog, Status-/Archiv-Regeln (EditPlanner → ChangeSet), Fehler mit Codes
  application/     Ports (Protocols) + kleine Use-Case-Services, Container
  infrastructure/  Adapter: markdown/ (Parser, Editoren, atomares Schreiben), database/ (SQLite), config/ (JSON), filesystem/
  api/             FastAPI: v2-Router, Pydantic-Schemas, Fehler → HTTP ({code, message, details})
  bootstrap.py     Composition Root: setzt alles per Konstruktor-Injection zusammen
web/               React + Vite + TypeScript, TanStack Query
  src/api/         aus OpenAPI generierte Typen (schema.d.ts), Client, Query-Hooks
  src/domain/      Filter, Baum, Fortschritt, Edit-Regeln als reine Funktionen
  src/state/       UI-Zustand (Server = Datenbank über /api/v2/ui-state), Polling-Pause
  src/components/, src/views/
```

Ein Projekt liegt entweder in Markdown-Dateien oder in der zentralen
Datenbank (`infrastructure/database/`, SQLite); beide Adapter bestehen dieselbe
Contract-Suite (`backend/tests/contract/`). Datenbank-Projekte entstehen über
`POST /api/v2/sources` mit `{"backend": "database", "project": "…"}`.

## Entwicklung

```bash
python3.11 -m venv .venv && .venv/bin/pip install -r backend/requirements-dev.txt
npm --prefix web install
```

```bash
.venv/bin/python backend/main.py        # API + gebautes Frontend auf :5411 (Auto-Reload)
npm --prefix web run dev                # Vite auf :5173, proxyt /api auf :5411
scripts/check.sh                        # ruff, mypy --strict, import-linter, pytest, tsc, eslint, vitest
```

Nach Änderungen an der v2-API die TS-Typen neu erzeugen (ein Test schlägt
sonst fehl):

```bash
.venv/bin/python backend/scripts/export_openapi.py && npm --prefix web run gen:api
```

Die Characterization-Tests (`backend/tests/characterization`) prüfen die
geschriebenen Markdown-Dateien bytegenau gegen Golden-Files; bewusste
Änderungen mit `UPDATE_GOLDEN=1 .venv/bin/pytest` neu aufnehmen.
