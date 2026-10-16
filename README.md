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
markiert. Über ✎/✕ hinter einem Projekt wird es in den Einstellungen
geöffnet bzw. der Eintrag entfernt; dort stehen Name (✎ neben dem Namen), Ordner,
Spiegel und Sync (siehe unten). Ein „MD“ hinter dem Namen kennzeichnet ein Projekt,
dessen Primärquelle Markdown-Dateien sind; Datenbank-Projekte, der Normalfall, tragen
kein Kennzeichen. Ordner, die nicht (mehr) lesbar sind, bleiben ausgegraut mit
⚠ und Fehlermeldung in der Liste stehen. Ohne Projektname wird der Name des
umgebenden Git-Repos verwendet.

Die Projektliste liegt in der zentralen Datenbank `configs/todo.db`. Jedes
Projekt hat eine **Primärquelle**, die die Wahrheit hält: ein **Markdown-Ordner**
oder die **Datenbank**. Die andere Seite darf als **Spiegel** geführt werden
(Datenbank-Spiegel eines Markdown-Ordners oder ein Markdown-Ordner zu einem
Datenbank-Projekt); der Spiegel wird nur durch einen Sync geschrieben, nie
automatisch. Beim Hinzufügen wählst du die Primärquelle (Vorauswahl im
Einstellungsmenü); Datenbank-Projekte tragen in der Liste das Kürzel „DB“. Der
Sync gleicht **pro Eintrag** ab und zeigt erst eine **Vorschau**: was nur in
der Datenbank geändert oder neu ist, geht in den Ordner, was nur im Ordner
geändert oder neu ist, in die Datenbank (neu, geändert, unverändert). Ein
Eintrag, der auf beiden Seiten geändert, auf beiden neu oder auf einer Seite
gelöscht wurde, ist ein **Konflikt**: er wird nie überschrieben oder gelöscht, die
Vorschau liefert beide Fassungen, und du entscheidest je Konflikt (Datenbank gilt,
Datei gilt oder aufschieben; ohne Entscheidung bleibt er unberührt und wird wieder
gemeldet). Der Sync-Dialog lädt die Vorschau beim Öffnen von selbst, zeigt die
Konflikte zuerst (je Zeile die unterschiedlichen Felder in einer Zeile, der volle
Vergleich per Klick) und die übrigen Änderungen als eine Zeile mit „Details“. Eine
Entscheidung lässt sich für jeden Konflikt einzeln treffen oder für alle
Änderungen auf beiden Seiten auf einmal; Löschungen nehmen die Sammel-Knöpfe aus
und brauchen eine eigene Entscheidung. Dann **Entscheidungen übernehmen** bzw.
**Ausführen**. Die Richtung kann auf eine Seite eingeschränkt werden (Einstellungen
→ Projekte → Einrichtung). Vor einem Sync in die Datenbank sichert der
Dienst die Datenbank (`configs/backups/todo-<Zeit>-sync.db`, ebenso vor einer
Schema-Migration; die letzten 10 bleiben).

**Notes im Sync:** Topics, Notes (samt Links, Auslösern, Archiv- und Papierkorbstand) und ihre Dokumente laufen im
selben Sync wie der Backlog (Vorschau, Konflikte, Entscheidungen im selben Dialog); die Dateien liegen im Unterordner
`notes/` des Markdown-Ordners (Format: [Schnittstellen](docs/techdocs/interfaces.md)). So lassen sich Notes über Git
zwischen Rechnern und in die Cloud (claude.ai) mitnehmen. Eine in den Dateien angelegte Note ohne Label
(`new-<kurzname>.md`) bekommt beim Import ihr Label.

**Auto-Sync:** Pro Projekt mit Spiegel lässt sich in Einstellungen → Projekte →
Einrichtung beim Spiegel „Ein, Sync automatisch“ wählen (Standard: „Ein, Sync von
Hand“). Der Viewer gleicht dann alle
`AUTO_SYNC_INTERVAL` Sekunden (Standard 30) von selbst ab, was nur eine Seite
geändert hat, löscht nie und überträgt keine Konflikte; die bleiben offen (Zahl in
der Projektkarte, ⚠ in der Sidebar), bis du sie im Sync-Dialog mit Vergleichsansicht
entscheidest. Ein Pull wird abgewartet, Dateien mit Git-Merge-Markern oder ein
fehlender Ordner pausieren das Projekt. Beim **Wechsel der Primärquelle** (Einstellungsmenü →
Projekte) wird vorher synchronisiert und ein Backup der bisherigen
Primärquelle angelegt; danach bleibt die bisherige Seite als Spiegel, die
Item-IDs bleiben gleich. Dieselben Schritte gibt es über die API
(`/api/v2/sources`, `/sources/{id}/sync`, `/sources/{id}/sync-status`).
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

## Einstellungen

Das Zahnrad oben in der Sidebar öffnet das Einstellungsmenü. Im Abschnitt
„Allgemein“ stehen Typ, Ort und Schema-Version der zentralen Datenbank (nur zur
Anzeige; der Ort steht in `configs/config.json`) und der Speicherort, mit dem
„Projekt hinzufügen“ vorbelegt ist (Markdown-Ordner oder Datenbank).

Im Abschnitt „Projekte“ steht pro Projekt eine Karte. Oben der Name mit dem Stand
des Spiegels (grün: in Sync, gelb: braucht dich, grau: nicht gespiegelt), darunter
Primärquelle und Spiegel nebeneinander (Datenbank oder Markdown-Ordner mit Pfad)
und der letzte Sync. Die Karte stellt genau eine Aktion nach vorn: „Sync starten…“,
„Konflikte klären…“ in einem gelben Hinweis, solange Konflikte offen sind (öffnet
den Sync-Dialog mit den Konflikten an erster Stelle), oder
„Datenbank-Spiegel einschalten“ bzw. „Markdown-Spiegel einschalten“ bei einem
Projekt ohne Spiegel (fehlt der Markdown-Ordner, „Spiegel-Ordner festlegen…“). Die
selteneren Einstellungen stehen unter „Einrichtung“ (eingeklappt): Markdown-Ordner,
der Spiegel als eine Auswahl („Aus“, „Ein, Sync von Hand“, „Ein, Sync automatisch“;
die Wahl setzt Spiegel und Auto-Sync in einer Änderung, „Aus“ schaltet auch den
Auto-Sync ab; ein Markdown-Ordner bleibt beim Ausschalten gespeichert und lässt
sich ohne neue Wahl wieder einschalten), die Sync-Richtung (beide
Richtungen, nur Datenbank → Ordner oder nur Ordner → Datenbank; gilt für Syncs aus
der Oberfläche und wird wie die Filter im UI-Zustand gespeichert, der Auto-Sync läuft
immer in beide Richtungen) und der Wechsel der Primärquelle
(„Zu Markdown wechseln…“ bzw. „Zur Datenbank wechseln…“: erst Sync, vorher ein
Backup der bisherigen Primärquelle unter `configs/backups/`). Ein ⚠ hinter dem
Projektnamen in der Sidebar heißt: der Spiegel wurde seit dem letzten Sync
geändert (oder ist nicht lesbar); ein Klick öffnet die Karte dieses Projekts. Ein ↻
hinter dem Projektnamen heißt: der Auto-Sync ist für dieses Projekt an. Der
Stand wird beim Laden der Seite, bei Fensterfokus, beim Öffnen des Menüs, mit
„Status prüfen“ und nach einem Sync geholt, nicht im Takt der Anzeige. Das
Bearbeiten (✎) in der Sidebar führt zur Karte des Projekts, auf der auch der Name
geändert wird; Entfernen und die Reihenfolge bleiben in der Sidebar.

## Sprache

Status, Prioritäten, Typen und Feldnamen sind in den Dateien englisch und
bleiben es. Der DE/EN-Schalter oben in der Sidebar übersetzt nur die Anzeige
(inkl. der gesamten Oberfläche); gefiltert und gespeichert wird immer mit den
englischen Werten. Alte deutsche Prioritäten (`Dringend`, `Wichtig`,
`Perspektivisch`) werden beim Lesen auf `Urgent`, `Important`, `Prospective`
abgebildet.

## Views

Die Sidebar links ist für alle Views gleich aufgebaut: Suche und Projektliste stehen
immer dort, darunter die Filter des aktiven Tabs. Baum, Abhängigkeiten und Kanban
filtern nach Status und Priorität des Backlogs, Notes nach den Note-Status, der
Papierkorb nur nach Suche und Projekten. Die Suche gilt für alle Tabs gemeinsam.

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
- **Papierkorb**: Gelöschte Items der in der Sidebar gewählten Projekte mit Löschdatum,
  gefiltert nach dem Suchtext.
  „Wiederherstellen“ holt ein Item samt Kindern zurück, „Endgültig löschen“
  entfernt es nach einer Bestätigung samt Kindern, Notizen und Specs (beides als
  Icon-Buttons in der Zeile). Mit den Checkboxen vor den Zeilen und dem Haken oben
  (alle an/ab) lassen sich mehrere Items wählen und gemeinsam wiederherstellen oder
  nach einer Bestätigung endgültig löschen. Ist ein Item mit seinem Vorfahren gewählt,
  wird nur der Vorfahre angefragt; was nicht klappt, wird mit Grund genannt.
- **Notes**: Gedanken mit Wiedervorlage, getrennt vom Backlog. Die Notes stehen wie das
  Backlog in einem Baum: Projekt → Topic → Unter-Topic → Note, Notes ohne (bekanntes)
  Topic unter „Ohne Topic“ am Projekt, aufgebaut wie der Backlog-Baum: eine Zeile je Knoten mit
  Punkt, Kennzeichen „Topic“ bzw. „Note“ (in der Statusfarbe, Status im Hovertext) und
  „Label — Kurzfassung“. Unter jedem Projekt trennt ein durchgehender Balken die Projekte.
  Mit „Erweiterte Markierung“ (Checkbox oben, gespeichert, Standard an) ist der Bereich eines
  Topics der ersten Ebene samt Inhalt hellgrau hinterlegt und links blau gekantet, der eines
  Topics der zweiten Ebene noch heller mit grauer Kante; ohne Haken bleibt der schlichte Baum. Knoten sind auf- und zuklappbar, „Topics zuklappen“ klappt alle (gespeichert wie
  im Backlog-Baum; beim Suchen ist alles offen, eine von anderswo geöffnete Note klappt
  ihren Zweig auf), leere Topics bleiben sichtbar, die Zahl ist die Summe der gezeigten
  Notes samt Unter-Topics, fällige zuerst. Die Aktionen eines Topics (neue Note darin,
  Unter-Topic, Umbenennen, Termin, Verschieben, Löschen) erscheinen als Icons beim
  Überfahren der Zeile, am Projekt „Neue Note ohne Topic“ und „Neues Topic“. Status, Projekte und Suchtext
  wählt die Sidebar: die Note-Status (wartet, fällig, zurückgestellt, erledigt, verworfen,
  befördert) sind beliebig kombinierbar, standardmäßig sind die offenen angehakt. Der
  Server filtert über `GET /notes/index` nach den Status (abgeschlossene liest er aus dem
  Archiv) und bei genau einem Projekt nach dem Projekt; Suche und mehrere Projekte filtert
  der Browser; bei einer Suche bleiben die Treffer, die Topics auf ihrem Weg und Topics,
  deren Name passt. Über dem Baum steht „Filter zurücksetzen“ (offene Status, leere Suche). Das Detail zeigt oben
  eine feste Leiste mit den Aktionen als Icon-Buttons (Bearbeiten, Befördern zu Epic,
  Story oder Task, Erledigen, Verwerfen, Zurückstellen, Behalten, Löschen, Großansicht,
  Schließen), darunter Kurzfassung, Topic-Pfad, Status, Prüf-Datum und Langtext (Markdown).
  Die Großansicht öffnet die Note fast vollbildschirmgroß mit Inhaltsverzeichnis aus den
  Überschriften; beim Bearbeiten steht die Vorschau neben dem Editor. Auslöser (Zeitpunkt,
  Ereignis „Item erreicht Status“, Termin des Topics), Links auf Items (auch anderer
  Projekte), Topics und Notes sowie Notizen und Specs wie beim Backlog sind einklappbare
  Abschnitte, deren Hinzufügen-Buttons in der Überschrift stehen. Ein Item zeigt im Detail
  die Notes, die auf es verweisen, und lässt sich über „Zur Note zurückstufen“ (nur im
  Status Open) zurück in eine Note verwandeln.
  Ein dezentes rotes Ausrufezeichen neben dem Titel zeigt die Zahl fälliger Notes (auch
  im Tab-Titel); ein Klick öffnet die Liste, gruppiert nach Grund (Auslöser,
  Änderungshinweis, Termin, Prüfung), mit den Aktionen je Note. Prüf-Intervall und
  Topic-Tiefe stellt man im Einstellungsmenü unter „Allgemein“ ein.

Klick auf ein Item öffnet das Detail-Panel rechts mit allen geparsten Feldern
(inkl. aller Freitext-Felder wie `Implementation`, `Verification`, `Context` etc.).
Unter „Untergeordnet“ trägt jedes direkte Kind Rahmen und Punkt in der Farbe
seines Status (Tooltip: Titel und Status); Kinder im Papierkorb stehen
gestrichelt und durchgestrichen am Ende (Tooltip: Löschdatum).

## Architektur

Onion-Architektur im Backend: Abhängigkeiten zeigen nur nach innen, geprüft
per `import-linter`.

```
src_old/backend/todo_viewer/
  domain/          Item, Source, Backlog, Status-/Archiv-Regeln (EditPlanner → ChangeSet), Fehler mit Codes
  application/     Ports (Protocols) + kleine Use-Case-Services, Container
  infrastructure/  Adapter: markdown/ (Parser, Editoren, atomares Schreiben), database/ (SQLite), config/ (JSON), filesystem/
  api/             FastAPI: v2-Router, Pydantic-Schemas, Fehler → HTTP ({code, message, details})
  bootstrap.py     Composition Root: setzt alles per Konstruktor-Injection zusammen
src_old/web/               React + Vite + TypeScript, TanStack Query
  src/api/         aus OpenAPI generierte Typen (schema.d.ts), Client, Query-Hooks
  src/domain/      Filter, Baum, Fortschritt, Edit-Regeln als reine Funktionen
  src/state/       UI-Zustand (Server = Datenbank über /api/v2/ui-state), Polling-Pause
  src/components/, src/views/
```

Die Primärquelle eines Projekts liegt entweder in Markdown-Dateien oder in der
zentralen Datenbank (`infrastructure/database/`, SQLite); die andere Seite kann
als Spiegel mitgeführt werden. Beide Adapter bestehen dieselbe Contract-Suite
(`src_old/backend/tests/contract/`), als Primärquelle und als Spiegel. Datenbank-Projekte
entstehen über `POST /api/v2/sources` mit `{"backend": "database", "project": "…"}`.

## Entwicklung

```bash
python3.11 -m venv .venv && .venv/bin/pip install -r src_old/backend/requirements-dev.txt
npm --prefix src_old/web install
```

```bash
.venv/bin/python src_old/backend/main.py        # API + gebautes Frontend auf :5411 (Auto-Reload)
npm --prefix src_old/web run dev                # Vite auf :5173, proxyt /api auf :5411
scripts/check.sh                        # ruff, mypy --strict, import-linter, pytest, tsc, eslint, vitest
```

Nach Änderungen an der v2-API die TS-Typen neu erzeugen (ein Test schlägt
sonst fehl):

```bash
.venv/bin/python src_old/backend/scripts/export_openapi.py && npm --prefix src_old/web run gen:api
```

Die Characterization-Tests (`src_old/backend/tests/characterization`) prüfen die
geschriebenen Markdown-Dateien bytegenau gegen Golden-Files; bewusste
Änderungen mit `UPDATE_GOLDEN=1 .venv/bin/pytest` neu aufnehmen.
