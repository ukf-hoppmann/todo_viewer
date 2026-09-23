# ToDo Viewer

Lokale Web-UI zum Visualisieren von `TODO.md`-Backlogs im "backlog format version 2"
(wie in `LLM_Tests`, `EZF-Backend`, `Agent_Harness`, `my_story_game` verwendet) plus
Fallback für einfache Markdown-Checklisten (`- [ ] Task`).

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
./todo.sh logs      # Live-Logs
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

Alternativ direkt in `configs/config.json`:

```json
{
  "sources": [
    { "project": "MeinProjekt", "path": "/absoluter/pfad/zu/docs/todo" }
  ]
}
```

Ältere Einträge, die noch auf eine Datei zeigen, werden beim Laden
automatisch auf deren Ordner umgestellt.

Änderungen an `config.json` oder den Backlog-Dateien werden automatisch
übernommen — das Frontend pollt `/api/v2/backlog` alle 5 Sekunden neu
(pausiert, solange ein Dialog offen ist oder ein Feld bearbeitet wird).

Der `configs/`-Ordner ist per Volume in den Container gemountet und liegt
physisch auf dem Host — er übersteht `./todo.sh down` und Rebuilds. Neben
`config.json` liegt dort auch `ui_state.json`, in dem der UI-Zustand
(ausgeblendete Filterwerte, Ansicht, Auswahl, Sprache) gespeichert wird.

## Bearbeiten

Status und Priorität sind im Detail-Panel editierbar. Wird ein Eintrag auf
`Completed` oder `Rejected` gesetzt, fragt die UI nach einer `Resolution`
und verschiebt ihn nach `archive.md`; ein Zurücksetzen auf einen offenen
Status holt ihn (ohne Resolution) zurück nach `TODO.md`. `Notes` und `Spec`
eines Eintrags öffnen sich in einem großen Lese-Popup.

Geschrieben wird atomar (temporäre Datei + Umbenennen), Zeilenenden (LF/CRLF)
bleiben erhalten. Hat jemand anderes (z. B. ein Agent) die Datei zwischen
Lesen und Schreiben geändert, bricht das Speichern mit einem Hinweis ab,
statt dessen Änderung zu überschreiben.

## Sprache

Status, Prioritäten, Typen und Feldnamen sind in den Dateien englisch und
bleiben es. Der DE/EN-Schalter oben in der Sidebar übersetzt nur die Anzeige
(inkl. der gesamten Oberfläche); gefiltert und gespeichert wird immer mit den
englischen Werten. Alte deutsche Prioritäten (`Dringend`, `Wichtig`,
`Perspektivisch`) werden beim Lesen auf `Urgent`, `Important`, `Prospective`
abgebildet.

## Views

- **Baum**: Epic → Story → Task Hierarchie pro Projekt, mit Fortschrittsbalken.
  Optionale Kinder (`Required for parent: No`) sind gestrichelt angebunden,
  gedimmt und haben einen hohlen Status-Punkt; sie zählen nicht zum Fortschritt.
- **Abhängigkeiten**: Gerichteter Graph aus dem `Dependencies`-Feld (zeigt nur
  Tasks mit tatsächlichen Abhängigkeiten, isolierte Tasks werden ausgeblendet).
- **Kanban**: Spalten nach Status (Open, In progress, Awaiting confirmation,
  Completed, Rejected).

Klick auf ein Item öffnet das Detail-Panel rechts mit allen geparsten Feldern
(inkl. aller Freitext-Felder wie `Implementation`, `Verification`, `Context` etc.).

## Architektur

Onion-Architektur im Backend: Abhängigkeiten zeigen nur nach innen, geprüft
per `import-linter`.

```
backend/todo_viewer/
  domain/          Item, Source, Backlog, Status-/Archiv-Regeln (EditPlanner → ChangeSet), Fehler mit Codes
  application/     Ports (Protocols) + kleine Use-Case-Services, Container
  infrastructure/  Adapter: markdown/ (Parser, Editoren, atomares Schreiben), config/ (JSON), filesystem/
  api/             FastAPI: v2-Router, Pydantic-Schemas, Fehler → HTTP ({code, message, details})
  bootstrap.py     Composition Root: setzt alles per Konstruktor-Injection zusammen
web/               React + Vite + TypeScript, TanStack Query
  src/api/         aus OpenAPI generierte Typen (schema.d.ts), Client, Query-Hooks
  src/domain/      Filter, Baum, Fortschritt, Edit-Regeln als reine Funktionen
  src/state/       UI-Zustand (Server = configs/ui_state.json), Polling-Pause
  src/components/, src/views/
```

Ein anderer Speicher (z. B. SQLite) wäre ein neuer Adapter für den Port
`BacklogRepository` und eine Zeile in `bootstrap.py`.

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
