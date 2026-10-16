# EPIC-007 — Architektur des Neubaus

Diese Spec ist die gemeinsame Grundlage aller Kinder von `EPIC-007`. Jede
Kind-Spec verweist auf die Abschnitte hier und legt nur fest, was darüber
hinausgeht. Entscheidungen und ihre Herkunft stehen in `EPIC-007_notes.md`,
die Ideensammlung in der Note `NOTE-002`.

## 1. Ziel

Der ToDo-Viewer wird neu gebaut: ein leerer Core als Hülle, die Fachlichkeit
in Plugins, im Backend und im Frontend. Die Datenbank speichert relational und
ist die Wahrheit. Ein Markdown-Spiegel je Projekt hält dieselben Daten als
Dateien, damit eine LLM in der Cloud ohne API mit ihnen arbeiten kann. Ein
Sync bringt beide Seiten zusammen und lässt sich später abschalten. Neben der
HTTP-API gibt es einen MCP-Server für LLMs und einen SSE-Kanal vom Backend ins
Frontend.

Wiederverwendbarkeit gilt **innerhalb dieses Projekts** (Variante A): ein
neues Plugin steckt vorhandene Bausteine zusammen und konfiguriert sie, statt
sie neu zu bauen. Der Core wird kein eigenes Paket, bleibt aber frei von
Fachlichkeit.

## 2. Stack

- Backend: Python 3.11, FastAPI, SQLAlchemy Core, SQLite. Neu: das offizielle
  MCP-SDK für Python (`mcp`). Keine weiteren Laufzeit-Bibliotheken ohne
  Freigabe.
- Frontend: React 19, Vite, TypeScript, Redux Toolkit mit RTK Query,
  React Router, i18next, MUI (alles wie im ezf-ui-Core). Aus dem alten
  Frontend bleiben `@xyflow/react`, `elkjs`, `marked`, `dompurify`; TanStack
  Query und `openapi-fetch` entfallen. TypeScript-Typen der API werden mit
  `openapi-typescript` aus dem OpenAPI-Schema erzeugt. Drag & Drop ohne
  Bibliothek (HTML5-Drag-and-Drop).
- Kein Login, keine Benutzer. Der Dienst läuft nur lokal.

## 3. Ordner

Der Neubau entsteht neben dem alten Code im selben Repository. Der alte
Viewer (`backend/`, `web/`) läuft bis zum Umstieg unverändert weiter.

```
server/                         Backend (Python-Paket `viewer`)
  pyproject.toml                Abhängigkeiten, ruff, mypy, import-linter
  src/viewer/
    core/                       Hülle ohne Fachlichkeit (Abschnitt 5)
      domain/ application/ infrastructure/ api/
    plugins/
      workspace/ backlog/ notes/ alarms/
        domain/ application/ infrastructure/ api/
        plugin.py               Plugin-Definition (Abschnitt 6)
    app/
      composition.py            Composition Root: feste Plugin-Liste, Verdrahtung
      main.py                   Start (uvicorn)
client/                         Frontend
  package.json vite.config.ts tsconfig*.json eslint.config.js
  src/app/                      Composition Root: Plugin-Katalog, Start
  src/core/                     aus ezf-ui kopiert, ohne Login (Abschnitt 8)
  src/shared/                   gemeinsame UI-Bausteine, erzeugte API-Typen
  src/plugins/<id>/             plugin.json, index.ts, Seiten, Slices, API
tests/                          alle Tests des Neubaus (Skill claude-harness:testing)
  implementation/unit/server/…  spiegelt server/src/viewer/
  implementation/unit/client/…  spiegelt client/src/
  implementation/integration/server/…   echte SQLite-Datei, echte Ordner, Contract-Suiten
  implementation/system/        optional: Server starten, HTTP/MCP/SSE von außen
  fixtures/ helpers/ README.md
```

Der Entwicklungs-Server des Neubaus läuft auf Port **5412**, damit der alte
Viewer auf 5411 (und damit die Backlog-API des Harness) weiterläuft. Die neue
Datenbank ist `configs/viewer.db`, getrennt von der alten `configs/todo.db`.
Nach dem Umstieg läuft der Neubau auf 5411, die alten Ordner werden entfernt.

## 4. Schichten und Abhängigkeiten (Backend)

- Innerhalb des Core und innerhalb jedes Plugins gilt die Zwiebel:
  `api` | `infrastructure` → `application` → `domain`. `api` und
  `infrastructure` importieren einander nicht. `domain` und `application`
  kennen weder FastAPI, Pydantic, SQLAlchemy noch das MCP-SDK.
- `viewer.core` importiert kein Plugin. Ein Plugin importiert `viewer.core`
  und die öffentliche Schnittstelle (`viewer.plugins.<id>` bzw. dessen
  `application`-Ports) der Plugins aus seinem `requires`, sonst nichts.
- Nur `viewer.app.composition` kennt alle Plugins und verdrahtet sie per
  Konstruktor-Injektion. Keine globalen Singletons, kein DI-Framework.
- Geprüft mit import-linter (Verträge in `server/pyproject.toml`).

Frontend: die Regeln 1–5 und 7 des ezf-ui (`app` → `core`, `shared`,
Plugins; `core` → `shared`; Plugin → `core`, `shared`, Plugins aus
`requires`; öffentliche API nur über `index.ts`; Slots; ein Besitzer je
Store-Slice und Endpunkt; Test-IDs `<owner>.<element>`). Geprüft mit der
ESLint-Regel `architecture/boundaries`, kopiert aus ezf-ui.

## 5. Backend-Core

Der Core bietet Ports und Mechanismen, keine Fachlichkeit:

| Baustein | Aufgabe |
|---|---|
| Plugin-Host | lädt die Plugin-Definitionen aus der festen Liste der Composition Root, prüft `requires` (unbekannt, Zyklus) und Eindeutigkeit von Namen, Routen, Tools, Tabellen-Präfixen; ein fehlerhaftes Plugin verhindert den Start mit klarer Meldung |
| Operationen | eine Operation wird einmal beschrieben (Abschnitt 6) und daraus HTTP-Route und MCP-Tool erzeugt |
| HTTP-Host | FastAPI-App; Routen unter `/api/<owner>/…`; Fehler als `{code, message, details}`; OpenAPI-Schema |
| MCP-Host | MCP-Server (Streamable HTTP) unter `/mcp`; Tools `<owner>_<operation>`; Fehler mit demselben `code` |
| Ereignisse | `EventBus`-Port: `publish(Event(topic, payload))`, synchrone Abonnenten im Prozess; Topics `<owner>.<name>` |
| SSE | `GET /api/core/events`: leitet öffentliche Ereignisse als Server-Sent Events weiter (`event: <topic>`, `data: <json>`), Keep-alive alle 15 s; keine Zustellgarantie, der Client lädt nach einem Neuverbinden neu |
| Uhr | `Clock`-Port (`now()` in UTC); Tests geben eine feste Uhr |
| Zeitgeber | `Scheduler`-Port: genau ein Termin je Besitzer (`schedule(owner, at, callback)`, ersetzt den vorigen), läuft nur im laufenden Server; kein Polling |
| Datenbank | Infrastruktur Datenbank (Abschnitt 7.1) |
| Dateien | Infrastruktur Dateien (Abschnitt 7.2) |
| Sync | generischer Sync-Dienst (Abschnitt 7.3) |
| Backups | Datenbank-Sicherung vor Migrationen und vor jedem Sync in die DB; die letzten 10 bleiben |
| UI-Zustand | `GET/PUT /api/core/ui-state/{owner}`: ein JSON-Dokument je Besitzer, ersetzt Browser-Speicher |
| Einstellungen | Konfiguration aus `configs/viewer.json` und Umgebungsvariablen; Plugin-Einstellungen unter `plugins.<id>` |
| Logging | strukturiertes Log nach `logs/viewer.log`, Request-ID je Anfrage |
| Fehler | `DomainError` mit stabilem `code`; Umwandlung nur im HTTP- bzw. MCP-Host |

## 6. Plugin-Vertrag (Backend)

Jedes Plugin exportiert aus `plugin.py` genau eine `PluginDefinition`:

- `id` (kebab-case, gleich dem Ordnernamen), `requires` (Liste von IDs),
- `migrations`: geordnete Liste vorwärts gerichteter Migrationen der eigenen
  Tabellen (Präfix `<id>_`, Bindestriche als `_`),
- `element_kinds`: die Elementtypen, die das Plugin im Element-Register
  anmeldet (nur Plugins, die `workspace` verlangen),
- `operations`: Liste von `Operation`,
- `mirror`: optional ein `MirrorCodec` und ein `SyncParticipant` (Abschnitt 7.3),
- `subscriptions`: Ereignis-Abonnements,
- `build(context) -> PluginServices`: baut die Dienste des Plugins aus dem
  Kontext, den die Composition Root übergibt (Ports des Core und der
  verlangten Plugins).

`Operation` beschreibt einen Anwendungsfall einmal:

```python
@dataclass(frozen=True)
class Operation:
    name: str                 # snake_case, eindeutig je Plugin
    summary: str              # erscheint in OpenAPI und als MCP-Beschreibung
    kind: Literal["read", "write"]
    input: type               # dataclass; JSON-Schema über pydantic.TypeAdapter im Host
    output: type              # dataclass oder Liste davon
    handler: Callable[..., Any]
    http: HttpBinding | None  # Methode + Pfad unter /api/<owner>
    mcp: bool = True          # als MCP-Tool <owner>_<name> veröffentlichen
```

Ein Plugin schreibt keine FastAPI-Router und keine MCP-Tools von Hand.
Schreibende Operationen nehmen einen `version`-Token und brechen bei einer
fremden Änderung mit `version_conflict` ab.

## 7. Speicher

### 7.1 Infrastruktur Datenbank

- SQLite über SQLAlchemy Core, Fremdschlüssel eingeschaltet, jede Operation in
  einer Transaktion.
- Migrationen je Besitzer (`core` und jedes Plugin), nur vorwärts, Stand in
  `core_migrations(owner, version)`. Vor jeder Migration ein Backup.
- Das Schema ist fest: keine freien Zusatzfelder. Neues kommt als Migration.
- Ein Plugin schreibt nur seine eigenen Tabellen. Fremdschlüssel dürfen nur
  auf Tabellen von Plugins aus `requires` zeigen (in der Praxis auf
  `workspace_elements.uid`). Fremde Daten liest es nur über Ports.
- Feste Wertelisten sind Nachschlagetabellen mit Fremdschlüssel, z. B.
  `backlog_priorities` mit genau `Urgent`, `Important`, `Normal`,
  `Prospective`.
- Optimistische Sperre: jedes Element hat eine `revision`; der
  `version`-Token der API ist daraus abgeleitet.

### 7.2 Infrastruktur Dateien

- Liest einen Ordner als Menge von Dateien mit Inhalt und Version (Hash).
- Schreibt atomar (temporäre Datei + Umbenennen), behält Zeilenenden (LF/CRLF)
  und bricht mit `mirror_conflict` ab, wenn sich eine Datei seit dem Lesen
  geändert hat.
- Erkennt Git-Merge-Marker und laufende Git-Operationen (`.git/*.lock`) und
  meldet sie, statt zu lesen.
- Kennt keine Formate. Die Formate liefern die Plugins (Codec).

### 7.3 Sync

Der Sync ist ein Anwendungsdienst des Core über zwei Ports; er kennt weder SQL
noch Dateien und weiß nicht, was ein Item oder eine Note ist.

- Jedes spiegelnde Plugin liefert
  - einen `MirrorCodec`: Dateien → Einträge (`MirrorEntry`) und Einträge →
    Dateien; er prüft das Format und weist ungültige Werte ab (z. B. eine
    unbekannte Priorität), mit Datei und Zeile;
  - einen `SyncParticipant`: Einträge aus der DB lesen und Änderungen in die
    DB schreiben (in einer Transaktion).
- `MirrorEntry`: `uid` (oder keine bei neuen Einträgen aus Dateien), `kind`,
  `label` (oder Platzhalter), kanonische Felder, Inhalts-Hash.
- Zuordnung nur über die `uid`. Das Label ist Anzeige.
- Vergleich je Eintrag mit dem Stand beim letzten Sync
  (`core_sync_state(project, uid, hash, synced_at)`): nur eine Seite geändert →
  übertragen; beide geändert, beide neu mit verschiedenem Inhalt oder auf einer
  Seite gelöscht → Konflikt, nie überschrieben oder gelöscht; der Besitzer
  entscheidet je Konflikt (Datenbank, Datei, aufschieben).
- Ein Eintrag aus den Dateien ohne `uid` ist neu: die DB vergibt `uid` und
  Label, ersetzt Platzhalter-Verweise und schreibt den Eintrag mit beidem
  zurück in die Dateien.
- Manueller Sync: Vorschau mit Token, dann Ausführen mit Entscheidungen;
  Richtung pro Lauf einschränkbar; Löschungen nur mit eigener Entscheidung.
- Auto-Sync je Projekt (Standard aus): überträgt nur konfliktfreie Änderungen,
  löscht nie, pausiert bei Merge-Markern, unlesbaren Dateien oder fehlendem
  Ordner, sichert vorher die DB.
- Status je Projekt ohne Datenänderung abfragbar (`in_sync`,
  `primary_changed`, `mirror_changed`, `both_changed`, `conflicts`,
  `paused`); Änderungen werden per SSE gemeldet (`core.sync.state`).
- Die DB ist immer die Wahrheit, Markdown immer der Spiegel. Ohne Spiegel
  läuft alles nur auf der DB; der Sync lässt sich je Projekt abschalten.

## 8. Frontend-Core

- Kopie des ezf-ui-Core (`src/core`): Plugin-Registry, Manifest-Prüfung,
  Slots, Store, Verbindung und `createPluginApi`, Fehler, Banner, Modals,
  Logging, i18n. Das Login (`core/auth`) und alles, was davon abhängt, fällt
  weg.
- Die aktiven Plugins kommen aus einer festen Liste in `src/app`
  (zunächst alle).
- Layout-Plugin `layout-header-sidebar` (aus ezf-ui): Kopfzeile mit den
  Hauptrouten als Tabs, Sprachschalter, Zähler (Slot `layout.header-actions`);
  Seitenleiste mit Abschnitten (Slot `layout.sidebar-sections`), die je nach
  aktiver Hauptroute gezeigt werden. Dunkles Thema wie im heutigen Viewer.
- SSE: der Core öffnet `GET /api/core/events`, verbindet sich bei Abbruch neu
  und gibt jedes Ereignis an die Plugins weiter; ein Plugin bildet Topics auf
  RTK-Query-Tags ab, die neu geladen werden. Polling entfällt.
- UI-Zustand über `/api/core/ui-state/{owner}`, nicht im Browser-Speicher.
- Sprachen DE und EN. Gespeicherte Werte (Status, Priorität, Typ) sind
  englisch, die UI übersetzt.

## 9. Plugins

| Plugin | Inhalt | requires |
|---|---|---|
| `workspace` | Projekte; Element-Register (`uid`, Typ, Label, Projekt, Revision, Löschdatum); Label-Zähler je Projekt und Präfix; Verknüpfungen zwischen beliebigen Elementen (Rollen `reference`, `origin`, `trigger`); Papierkorb für alle Elementtypen; Spiegel- und Sync-Einstellungen je Projekt | – |
| `backlog` | Epics, Stories, Tasks; Baum; Abhängigkeiten; Notiz- und Spec-Dokumente; Status, Priorität, Bereich; Parent-Regeln; Typwechsel; Markdown-Codec | `workspace` |
| `notes` | Notes, Topics, Auslöser (Ereignis, Topic-Termin, Prüfdatum), Hinweise, Befördern/Zurückstufen; Markdown-Codec | `workspace`; für Befördern und Ereignis-Auslöser die öffentlichen Ports von `backlog` |
| `alarms` | Wecker: Zeitpunkt, Text, optionales Ziel-Element; Auslösung im Backend, Meldung per SSE; Markdown-Codec | `workspace` |

Frontend-Plugins tragen dieselben IDs; dazu kommt `layout-header-sidebar`.
Gemeinsame UI-Bausteine liegen in `src/shared` (Baum, Detailpanel,
Markdown-Editor mit Vorschau, Filterabschnitt, Dialoge) und tragen keinen
globalen Zustand. Der einheitliche Neu-Dialog gehört `workspace`: Plugins
melden ihre Elementtypen im Slot `workspace.create-types` an.

`notes` braucht `backlog` für das Befördern und für Ereignis-Auslöser. Damit
`backlog` nichts von `notes` weiß, meldet `backlog` Statuswechsel als Ereignis
`backlog.item.status_changed`; `notes` abonniert es.

## 10. Markdown-Format

Das Format („backlog format version 2“) wird in diesem Projekt festgelegt
(`TASK` Format v2) und in `docs/techdocs/interfaces.md` beschrieben. Kernpunkte:

- Aufbau wie Version 1: `TODO.md`, `archive.md`, `items/<ID>/`; dazu
  `notes/` (eine Datei je Note, `topics.md`) und `alarms.md`.
- Jeder Eintrag trägt eine Zeile `Uid: <uuid>.` Die vergibt die DB; eine
  LLM legt neue Einträge ohne `Uid` an.
- Neue Einträge ohne Label tragen einen Platzhalter `NEW-<kurzname>`
  (Backlog) bzw. stehen in `notes/new-<kurzname>.md` (Notes); der Import
  vergibt Label und `Uid` und schreibt Verweise um.
- `counters.md` entfällt; Labels vergibt nur die DB.
- Prioritäten nur `Urgent`, `Important`, `Normal`, `Prospective`; alles
  andere weist der Sync mit Datei und Zeile ab.

## 11. Agenten-Schnittstelle

HTTP-API und MCP entstehen aus denselben Operationen (Abschnitt 6). Der
Harness wird nach dem Umstieg vom Projektinhaber angepasst; dafür liefert
dieses Projekt die Formatbeschreibung und die Liste der MCP-Tools.

## 12. Was wegfällt

Kanban-Ansicht; Wahl der Primärquelle je Projekt (die DB ist immer die
Wahrheit); freie Zusatzfelder an Items; Polling im Frontend; `counters.md`;
Login aus dem ezf-ui-Core.

## 13. Kinder und Reihenfolge

Jedes Kind hat eine eigene Spec. Ein Kind beginnt erst, wenn seine Abhängigkeiten abgeschlossen sind. Offene Fragen sammelt `STORY-060`; ihre Annahmen gelten, bis der Projektinhaber anders entscheidet.

| Item | Titel | Abhängigkeiten |
|---|---|---|
| `STORY-060` | Noch zu klären: offene Fragen zum Neubau | – |
| `TASK-034` | Architekturregeln für den Neubau schreiben und freigeben lassen | – |
| `TASK-035` | Markdown-Format Version 2 festlegen | `TASK-034` |
| `STORY-061` | Server-Grundgerüst: Core mit Plugin-Host, HTTP, Ereignissen und SSE | `TASK-034` |
| `STORY-062` | MCP-Host: Operationen als MCP-Tools für LLMs | `STORY-061` |
| `STORY-063` | Infrastruktur Datenbank: Migrationen je Plugin, Transaktionen, Backups | `STORY-061` |
| `STORY-064` | Infrastruktur Dateien: atomares Schreiben, Konflikte, Merge-Marker | `STORY-061` |
| `STORY-065` | Generischer Sync-Dienst über Datenbank und Dateien | `STORY-063`, `STORY-064`, `TASK-035` |
| `STORY-066` | Client-Grundgerüst: ezf-ui-Core ohne Login, Layout, SSE, UI-Zustand | `STORY-061` |
| `STORY-067` | Gemeinsame UI-Bausteine für alle Plugins | `STORY-066` |
| `STORY-068` | Projekte, Suche und Element-Register (Plugin workspace) | `STORY-063`, `STORY-067` |
| `STORY-069` | Verknüpfungen zwischen Elementen | `STORY-068` |
| `STORY-070` | Papierkorb für alle Elementtypen | `STORY-068` |
| `STORY-071` | Backlog anzeigen: Baum, Filter, Suche, Detail (Plugin backlog) | `STORY-068` |
| `STORY-072` | Backlog bearbeiten: Felder, Formular, Anlegen, Typwechsel, Drag & Drop | `STORY-071` |
| `STORY-073` | Backlog-Dokumente: Notizen und Specs | `STORY-071` |
| `STORY-074` | Abhängigkeiten-Graph | `STORY-071` |
| `STORY-075` | Backlog im Markdown-Spiegel | `STORY-065`, `STORY-071`, `STORY-073` |
| `STORY-076` | Sync in der Oberfläche: Spiegel-Einstellungen, Sync-Dialog, Status | `STORY-075` |
| `STORY-077` | Notes und Topics (Plugin notes) | `STORY-069` |
| `STORY-078` | Notes-Auslöser, Änderungshinweise, Befördern und Zurückstufen | `STORY-077`, `STORY-072` |
| `STORY-079` | Notes im Markdown-Spiegel | `STORY-065`, `STORY-078` |
| `STORY-080` | Wecker (Plugin alarms) | `STORY-069`, `STORY-065` |
| `STORY-081` | KI-Schnittstelle vollständig: MCP und API für den Harness | `STORY-062`, `STORY-070`, `STORY-072`, `STORY-073`, `STORY-078`, `STORY-080` |
| `STORY-082` | Datenübernahme aus dem alten Viewer | `STORY-075`, `STORY-079`, `STORY-080`, `STORY-070` |
| `STORY-083` | Betrieb: Container, Start-Skript, Logs und Backups des Neubaus | `STORY-066` |
| `STORY-084` | Umstieg: der Neubau ersetzt den alten Viewer | `STORY-060`, `STORY-074`, `STORY-076`, `STORY-081`, `STORY-082`, `STORY-083` |
