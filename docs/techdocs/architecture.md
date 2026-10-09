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
| Routing-Adapter | Wählen je Projekt (`Source.backend`, Standard `markdown`) den Speicher-Adapter; unbekanntes Backend → Fehlercode `unknown_backend` | `backend/todo_viewer/infrastructure/routing.py` |
| Markdown-Adapter | Formaterkennung, Parser, Feld-Mapping, Editoren, Verschieben ins/aus dem Archiv, atomares Schreiben | `backend/todo_viewer/infrastructure/markdown/` |
| Datenbank-Adapter | Zentrale Datenbank (SQLAlchemy Core, SQLite): Projektliste und UI-Zustand, Items mit interner `uid` und Label, Verweise als Fremdschlüssel, Notizen/Specs an der `uid`, Schreiben in Transaktionen, versionierte Migrationen; übernimmt beim ersten Zugriff `sources` aus `config.json` und `ui_state.json` früherer Versionen (`config_import.py`) | `backend/todo_viewer/infrastructure/database/` |
| Notes-Adapter | Topics (Tiefe konfigurierbar, Standard 3), Notes, Links (auf Item per Projekt + Label, auf Topic oder Note), Auslöser und Dokumente von Notes; nur in der zentralen Datenbank, unabhängig von der Primärquelle des Projekts; Label-Zähler pro Projekt und Typ; Projektwechsel einer Note legt sie im Zielprojekt neu an. Port `NoteRepository`/`NoteDocumentStore`, Modell in `domain/notes.py`; der Adapter speichert nur, er enthält keine Auslöser-Logik. Archiv-Filter, Zurücksetzen der Auslöser, Papierkorb für Topics samt Notes und endgültiges Löschen sind Port-Methoden | `backend/todo_viewer/infrastructure/database/notes.py` |
| Notes-Logik | Ob ein Auslöser eingetroffen ist und ob eine Note fällig ist, entscheiden reine Funktionen mit der Zeit als Parameter (`trigger_arrived`, `evaluate` in `domain/notes.py`): Zeit- und Topic-Auslöser beim Lesen, Ereignis-Auslöser im Use Case, der einen Item-Status ändert (`ItemService.edit` → `NoteService.item_status_changed`); es gibt keinen Hintergrund-Takt. „Fällig“ wird abgeleitet und nie gespeichert (gespeichert: `waiting`, `snoozed`, `done`, `dropped`, `promoted`); eine fällige Note bleibt fällig, bis sie zurückgestellt, erledigt, verworfen oder gelöscht ist. Prüf-Datum 30 Tage (`notes.review_days`). Erledigt/verworfen/befördert → Archiv; Löschen → Papierkorb (Topics nur mit Kaskade), Wiederherstellen macht die Note wartend mit neuem Prüf-Datum; endgültiges Löschen (`purge_*`) gibt es nur im Service für den Besitzer, nicht über die API. Zurückstellen setzt gefeuerte Ereignis-Auslöser zurück und entfernt verstrichene Zeit-/Topic-Auslöser. Hinweise zwischen Notes und Items (`Notice` in `domain/notes.py`, Tabelle `note_notices`, Namen über Projekt plus Label) entstehen in den Use Cases, die ein Item ändern: `ItemService`, `TrashService` und `RetypeService` melden dem `ItemStatusListener` (`NoteService`) nach dem Schreiben Statuswechsel, Löschen und Typwechsel; `NoteService.finish` meldet verworfene und beförderte Notes an ihre Items. Ein offener Hinweis macht die Note fällig (Grund `notice`); entschieden wird über `NoteService.decide`. Fehler beim Anlegen eines Hinweises werden protokolliert und brechen die Änderung nicht ab. Weitere Use Cases: `TopicService` (Topics anlegen, ändern, verschieben), `NoteDocumentService` (Notizen und Specs einer Note), `NoteIndexService` (schlanker Index, Fällig-Zähler und -Liste über alle Projekte, ohne Langtexte) und `NotesSettingsService` (die zwei Optionen, in `config.json` gespeichert und ohne Neustart wirksam: die Services lesen sie bei jedem Aufruf) und `ConversionService` (Note zu Item befördern, Item zur Note zurückstufen; Regeln als reine Funktionen in `domain/conversion.py`). Item und Note liegen in verschiedenen Speichern ohne gemeinsame Transaktion: die neu entstehende Seite wird zuerst angelegt, der Link `origin` folgt sofort und belegt den ersten Schritt, jeder weitere Schritt prüft, was schon da ist, so dass eine Wiederholung nur Fehlendes nachholt (Entscheidungen in den Notes von `TASK-013` und `TASK-014`). Die HTTP-Routen stehen in `api/v2/notes_routers.py`, ihre Schemas in `notes_schemas.py` (siehe [Schnittstellen](interfaces.md)) | `backend/todo_viewer/domain/notes.py`, `domain/note_lifecycle.py`, `application/services/notes.py`, `topics.py`, `note_documents.py`, `note_index.py`, `note_settings.py`, `conversion.py`, `domain/conversion.py`, `api/v2/notes_routers.py` |
| Config-Adapter | `config.json` (`storage_url`); liest die JSON-Dateien früherer Versionen für deren Übernahme in die Datenbank | `backend/todo_viewer/infrastructure/config/` |
| Dateisystem-Adapter | Ordner-Browser, Projektname aus dem umgebenden Git-Repo | `backend/todo_viewer/infrastructure/filesystem/` |
| HTTP-API | FastAPI-Router `/api/v2`, Pydantic-Schemas, zentrale Fehlerübersetzung, Auslieferung von `web/dist` | `backend/todo_viewer/api/` |
| Logging | Konfiguration (structlog über das Standard-`logging`, auch für uvicorn), key=value-Zeilen, Rotation; Request-Middleware mit Request-ID und einer Zeile pro Request | `backend/todo_viewer/infrastructure/log_setup.py`, `backend/todo_viewer/api/request_log.py` |
| Composition Root | Setzt Adapter und Services per Konstruktor-Injection zusammen; liest Einstellungen aus der Umgebung | `backend/todo_viewer/bootstrap.py`, `backend/main.py` |
| Frontend | React 19 + Vite + TypeScript, TanStack Query; Views Baum, Graph (React Flow + ELK), Kanban, Notes (Topic-Baum mit Summen und Auf-/Zuklappen, Filterleiste (Status und fällig gehen als Query an `GET /notes/index`, ebenso das Projekt, wenn in der Projektliste der Sidebar genau eines gewählt ist; Suche, mehrere Projekte und Gruppierung im Browser), Notes-Liste, Detail mit fester Aktionsleiste aus `IconButton`s, Großansicht mit Inhaltsverzeichnis, Auslöser, Links und Dokumente als einklappbare `NoteSection`s; `NoteDetail` mit dem Markdown-Renderer wird erst beim Öffnen einer Note geladen, der `DocumentDialog` wird für Items und Notes über ein `DocumentBackend` genutzt), Papierkorb; rotes Ausrufezeichen (`DueBadge`, Zähler über `GET /notes/due/count` jede Minute und beim Fokussieren des Fensters, auch im Tab-Titel) und Fällig-Modal (`DueModal`, Liste nur bei geöffnetem Modal); Detail-Panel mit direkt änderbaren Feldern (Status, Priorität, Bereich, Pflicht für Parent, Abhängigkeiten) und Bearbeiten-Modus, Dialoge zum Anlegen, Löschen und für Dokumente; Einstellungsmenü (⚙ in der Sidebar) aus einer Abschnittsliste (`components/settings/sections.tsx`, ein neuer Abschnitt ist ein neuer Eintrag), „Allgemein“ (Datenbank lesend, Standard-Speicherort für neue Projekte) und „Projekte“ (Karte je Projekt: Primärquelle wechseln, Ordner, Spiegel, Sync-Stand, Sync mit Richtung; das ⚠ in der Sidebar öffnet die Karte; der Sync-Stand wird über `GET /sync-status` nur auf Anforderung geholt, `Modal` schließt bei Escape nur den obersten Dialog) | `web/src/` |
| Frontend-Domain | Filter, Baum, Fortschritt, Abhängigkeitsgraph, Edit-Regeln, Topic-Baum samt Summen, Suche und Gruppierung der Notes, Gliederung eines Markdown-Textes, Schnellwahlen zum Zurückstellen, Gruppierung der Fälligen, Tab-Titel und Beförderungs-Entwurf als reine Funktionen | `web/src/domain/` |
| API-Client | Aus dem OpenAPI-Schema generierte Typen (`schema.d.ts`), Client, Query-Hooks | `web/src/api/` |

## Datenfluss

- Lesen: Das Frontend pollt `GET /api/v2/backlog` alle 5 Sekunden (pausiert,
  solange ein Dialog offen ist oder ein Feld bearbeitet wird). Das Backend liest
  für jedes Projekt aus der Datenbank die `TODO.md` und – falls vorhanden –
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
- Notizen und Specs werden über Item-ID und Dokumentnamen adressiert (Port
  `DocumentStore`); ein Item listet seine Dokumente in `notes`/`spec` nur mit
  Namen. Dass sie in Markdown unter `items/<ID>/<Name>` liegen und bei einem
  Typwechsel samt Pfaden in `Notes:`/`Spec:` mitwandern, weiß nur der
  Markdown-Adapter (`infrastructure/markdown/document_paths.py`).
- Abhängigkeiten zeigen nur nach innen: `bootstrap` → `api` | `infrastructure`
  → `application` → `domain`.

## Zustand und Speicherung

- Backlog-Daten: je Projekt entweder in dessen Markdown-Dateien
  (`backend: markdown`, Standard) oder in der zentralen Datenbank
  (`backend: database`, `configs/todo.db`). Diese Primärquelle hält die
  Wahrheit. Die andere Seite darf als Spiegel geführt werden (`mirror`;
  Datenbank-Spiegel eines Markdown-Projekts: Spalte `mirror_database`,
  Markdown-Spiegel eines Datenbank-Projekts: `sync_path`); er wird nur durch
  einen Sync geschrieben, sonst gibt es keine weitere Kopie.
- Sync-Status: `SyncStatusService` (`application/services/syncstatus.py`)
  vergleicht die Fingerabdrücke (`domain/sync.py`: `fingerprint`, `classify`)
  beider Seiten jetzt mit denen direkt nach dem letzten Sync (`Source.baseline`,
  Spalten in `projects`). Aufgezeichnet wird nur, wenn der Sync über diesen
  Dienst läuft (nicht beim Backup); Lesen schreibt nie. Berechnet wird der
  Status nur auf Anforderung (`/sync-status`), nicht mit den Projektlisten.
- Abgleich Datenbank ⇄ Markdown: nur auf Anforderung (`POST /sources/{id}/sync`),
  nie automatisch. `SyncService` (`application/services/sync.py`) arbeitet mit
  denselben Ports auf zwei Quellen desselben Projekts (Datenbank und
  Markdown-Ordner am `sync_path`); der Vergleich (neu/geändert/fehlend, Token)
  liegt in `domain/sync.py`, geschrieben wird über `write_backlog` und die
  Dokument-Ports. Die Markdown-Seite rendert dafür alle Felder
  (`EntryRenderer.render_full`), den Text um die Einträge lässt sie stehen.
  Das Umstellen des Backends (`SourceService.update`) verlangt vorher einen
  Sync (`SyncService.in_sync`) und sichert die bisherige Primärquelle
  (`BackupService`: Byte-Kopie über den Port `RawBackup`, den der
  Markdown-Adapter erfüllt, sonst Export über `SyncService`) und tauscht nur die Ordnerseite: `path` ⇄
  `sync_path`, gleiche `source_id`; die bisherige Seite bleibt Spiegel. Ein
  Markdown-Projekt kann dazu per `from_md` in die Datenbank gelesen werden;
  mit Datenbank-Spiegel geht der Sync auch zurück (`to_md`).
- Projektliste (Name, Backend, Ordner, `sync_path`, Reihenfolge; `source_id` =
  UUID): zentrale Datenbank. Ort der Datenbank (`storage_url`): `configs/config.json`.
- UI-Zustand (ausgeblendete Filterwerte, eingeklappte Knoten, markierte
  Projekte, Ansicht, Auswahl, Suche, Sprache, im Notes-Bereich Projekt, Topic und geöffnete
  Note): zentrale Datenbank, über die API gelesen und geschrieben.
- Log: Datei aus `LOG_FILE` (im Container `./logs/` auf dem Host), nach Größe rotiert.
- Im Container liegt `configs/` per Volume auf dem Host; die Nachbar-Repos sind
  unter demselben absoluten Pfad beschreibbar eingebunden.

## Wichtige Entscheidungen

| Entscheidung | Kurzbegründung | Referenz |
|---|---|---|
| Onion-Architektur, Schichtregeln per `import-linter` | Fachregeln unabhängig von HTTP und Dateiformat; anderer Speicher = neuer Adapter + eine Zeile in `bootstrap.py` | `pyproject.toml`, [Architekturregeln](../development/architecture/backend.md) |
| Konstruktor-Injection ohne DI-Framework | Einfach nachvollziehbar, Services mit In-Memory-Fakes testbar | `backend/todo_viewer/bootstrap.py` |
| Atomares Schreiben mit Konflikterkennung | Parallele Änderungen (z. B. durch Agenten) werden nicht überschrieben | [Architekturregeln](../development/architecture.md) |
| Contract-Suite für die Speicher-Ports | Jeder Speicher-Adapter (Markdown, Datenbank und ein In-Memory-Fake) besteht dieselben Tests | `backend/tests/contract/`, `backend/tests/fakes.py` |
| Golden-Files für geschriebene Dateien | Dateiinhalte nach Edits bleiben bytegenau stabil | `backend/tests/characterization/` |
| Logging mit structlog, eine key=value-Zeile pro Ereignis | Fehleranalyse per `grep` ohne ganze Datei zu lesen; Kontext (Request-ID) ohne eigenen Code; Domain und Application loggen nicht, Fehler werden an der API-Grenze protokolliert | [STORY-016-Notizen](../todo/items/STORY-016/STORY-016_notes.md) |
| TS-Typen aus OpenAPI generiert | Frontend und API können nicht unbemerkt auseinanderlaufen (Test prüft Aktualität) | `backend/tests/api_v2/test_openapi.py` |
