# Architektur

<!-- Nur der aktuelle Stand. Historie gehört in die Tagesberichte, Begründungen
in die Backlog-Notizen. -->

## Überblick

Der ToDo Viewer ist eine lokale Web-Anwendung, die Markdown-Backlogs
(Claude_Harness-Backlog-Format: `TODO.md`, `archive.md`, `items/<ID>/`) aus
mehreren Projekten liest, als Baum,
Abhängigkeitsgraph oder Kanban anzeigt und Änderungen direkt in die Dateien
zurückschreibt: Items anlegen, bearbeiten, in den Papierkorb verschieben,
wiederherstellen oder endgültig löschen, Notizen und Specs schreiben. Ein Python-Backend
(FastAPI) stellt die API v2 bereit und liefert das gebaute React-Frontend aus.

## Komponenten

| Komponente | Verantwortung | Ort |
|---|---|---|
| Domain | Item, Source, Backlog, Status-/Archiv-Regeln (`EditPlanner` → `ChangeSet`), Fehler mit stabilen Codes; keine äußeren Abhängigkeiten | `backend/todo_viewer/domain/` |
| Application | Ports als Protocols (`BacklogRepository`, `SourceRepository`, `DocumentStore`, `FolderBrowser`, `ProjectNameSuggester`, `UiStateStore`), Use-Case-Services, `Container` | `backend/todo_viewer/application/` |
| Markdown-Adapter | Formaterkennung, Parser, Feld-Mapping, Editoren, Verschieben ins/aus dem Archiv, atomares Schreiben | `backend/todo_viewer/infrastructure/markdown/` |
| Config-Adapter | `config.json` (Quellen, inkl. Migration alter Dateipfade) und `ui_state.json` | `backend/todo_viewer/infrastructure/config/` |
| Dateisystem-Adapter | Ordner-Browser, Projektname aus dem umgebenden Git-Repo | `backend/todo_viewer/infrastructure/filesystem/` |
| HTTP-API | FastAPI-Router `/api/v2`, Pydantic-Schemas, zentrale Fehlerübersetzung, Auslieferung von `web/dist` | `backend/todo_viewer/api/` |
| Composition Root | Setzt Adapter und Services per Konstruktor-Injection zusammen; liest Einstellungen aus der Umgebung | `backend/todo_viewer/bootstrap.py`, `backend/main.py` |
| Frontend | React 19 + Vite + TypeScript, TanStack Query; Views Baum, Graph (React Flow + ELK), Kanban, Papierkorb; Detail-Panel mit Bearbeiten-Modus, Dialoge zum Anlegen, Löschen und für Dokumente | `web/src/` |
| Frontend-Domain | Filter, Baum, Fortschritt, Abhängigkeitsgraph, Edit-Regeln als reine Funktionen | `web/src/domain/` |
| API-Client | Aus dem OpenAPI-Schema generierte Typen (`schema.d.ts`), Client, Query-Hooks | `web/src/api/` |

## Datenfluss

- Lesen: Das Frontend pollt `GET /api/v2/backlog` alle 5 Sekunden (pausiert,
  solange ein Dialog offen ist oder ein Feld bearbeitet wird). Das Backend liest
  für jede Quelle aus `config.json` die `TODO.md` und – falls vorhanden –
  `archive.md` und gibt Quellen samt Items zurück. Neu gerendert wird nur bei
  geänderten Daten.
- Bearbeiten: `PATCH /api/v2/items/{source_id}/{item_id}` mit der zuletzt
  gelesenen `version` → `ItemService` holt das Item per ID über den Port
  `BacklogRepository` und vergleicht die Version → `EditPlanner` berechnet
  einen `ChangeSet` (bei `Completed`/`Rejected` mit Resolution und Verschieben
  ins Archiv, beim Zurücksetzen zurück) → der Markdown-Adapter sucht den
  Eintrag über seine ID, prüft die Version erneut unter Lock und schreibt
  atomar.
- Items werden überall nur über Quelle und ID adressiert; Dateien, Zeilen und
  Ablageorte kennt nur der Markdown-Adapter. Die Version ist ein Hash über den
  Inhalt des Items (Domain), damit ein anderer Speicher denselben Vertrag
  erfüllen kann.
- Abhängigkeiten zeigen nur nach innen: `bootstrap` → `api` | `infrastructure`
  → `application` → `domain`.

## Zustand und Speicherung

- Backlog-Daten: ausschließlich in den Markdown-Dateien der konfigurierten
  Projekte; der Viewer hält keinen eigenen Datenbestand.
- Quellen: `configs/config.json`.
- UI-Zustand (ausgeblendete Filterwerte, eingeklappte Knoten, markierte
  Projekte, Ansicht, Auswahl, Suche, Sprache): `configs/ui_state.json`, über die API gelesen und
  geschrieben.
- Im Container liegt `configs/` per Volume auf dem Host; die Nachbar-Repos sind
  unter demselben absoluten Pfad beschreibbar eingebunden.

## Wichtige Entscheidungen

| Entscheidung | Kurzbegründung | Referenz |
|---|---|---|
| Onion-Architektur, Schichtregeln per `import-linter` | Fachregeln unabhängig von HTTP und Dateiformat; anderer Speicher = neuer Adapter + eine Zeile in `bootstrap.py` | `pyproject.toml`, [Architekturregeln](../development/architecture/backend.md) |
| Konstruktor-Injection ohne DI-Framework | Einfach nachvollziehbar, Services mit In-Memory-Fakes testbar | `backend/todo_viewer/bootstrap.py` |
| Atomares Schreiben mit Konflikterkennung | Parallele Änderungen (z. B. durch Agenten) werden nicht überschrieben | [Architekturregeln](../development/architecture.md) |
| Golden-Files für geschriebene Dateien | Dateiinhalte nach Edits bleiben bytegenau stabil | `backend/tests/characterization/` |
| TS-Typen aus OpenAPI generiert | Frontend und API können nicht unbemerkt auseinanderlaufen (Test prüft Aktualität) | `backend/tests/api_v2/test_openapi.py` |
