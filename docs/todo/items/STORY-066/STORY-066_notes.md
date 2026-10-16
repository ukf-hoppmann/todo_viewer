# STORY-066 — Client-Grundgerüst: ezf-ui-Core ohne Login, Layout, SSE, UI-Zustand

## 2026-10-16 — Entscheidungen

### Decided

- Stack bleibt: React/Vite/TypeScript; im Frontend Redux Toolkit wie in ezf-ui.
- Der Frontend-Core wird aus ezf-ui kopiert; das Login fliegt raus.
- Layout ähnlich ezf-ui: Kopfzeile und Seitenleiste mit austauschbaren Elementen; die Seitenleiste bleibt.
- SSE als Rückkanal; Polling entfällt.

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Quelle.** `reference/ezf-ui/` (Commit `e851c691`) ist die Vorlage: `src/core`, `src/app`, `plugins/layout-header-sidebar`, `plugins/example`, `configs/eslint`, `configs/vite`, Tests und Test-Helfer. Kopiert und angepasst wird nach `client/` und `tests/` (`tests/implementation/unit/client/…`, `tests/helpers/client/`); die Pfade der kopierten Tests werden neu berechnet.
- **Was wegfällt.** `core/auth` (Login, Guard, `returnTo`), `core/config` (Dateien `config.json`/`plugins.json`; die Plugin-Auswahl ist eine feste Liste in `client/src/app`), die Auth-Teile von `createConnectionMonitor` und `createConnection` (kein 401/407, keine Cookies), das Ausgabe-Ziel `BackendSink` und `installBackendLogging` (der Neubau hat keine Log-Schnittstelle; Logs gehen an die Konsole), `ColorSchemeMenu` (das Thema ist fest dunkel) und die Sprache Französisch (nur DE und EN, EPIC-007-Spec §8).
- **Fehlerform der Verbindung.** Ein Fehlerantwort `{code, message, details}` des Servers wird in `ConnectionError.body` erkannt; `core/errors` und die Banner übersetzen den `code` (Schlüssel `errors.<code>` im Namensraum `core` und des Besitzers), nicht die Meldung.
- **Layout als Plugin.** `layout-header-sidebar` besitzt die Slots `layout-header-sidebar.header-actions` (Elemente der Kopfzeile, z. B. Zähler) und `layout-header-sidebar.sidebar-sections` (Abschnitte der Seitenleiste mit `when: ["<owner>/<name>", …]`, den Hauptrouten, bei denen sie erscheinen). Die Architekturregel verlangt `<owner-id>.<name>` mit der Plugin-ID als Besitzer; die Spec nennt kurz `layout.header-actions`. Siehe Frage 19 in `STORY-060`. Damit der Core die Kopfzeile und die Seitenleiste nicht selbst kennt, bekommt die Plugin-Definition ein optionales Feld `frame` (ein Rahmen-Bauteil um die Routen); ohne Layout-Plugin zeigt der Core den bisherigen schlichten Rahmen aus `RootLayout` und Tabs.
- **Neue Plugin-Felder** (Erweiterung des Vertrags): `slots` (die eigenen Slots mit Namen), Widget-Beiträge `{slot, name, component, order?, when?}` zu solchen Slots und zu den Slots des Core (`core.settings-sections`), `eventHandlers` (`topic → (payload, {dispatch, api}) => void`) und `frame`.
- **SSE.** `core/events`: `EventSource('/api/core/events')`, Neuverbinden mit Backoff, nach dem Neuverbinden das Ereignis `core.reconnected` an alle Plugins; Verteilung nur an aktive Plugins mit passendem Handler.
- **UI-Zustand.** Die API des Core (`core.api`, `createPluginApi('core', …)`) liest und schreibt `/api/core/ui-state/{owner}`; `usePersistentState(owner, key, default)` hält den Wert sofort lokal (optimistisch im Cache) und schreibt entprellt das ganze Dokument zurück. Der Browser-Speicher wird nicht benutzt: der Sprachdetektor von i18next bekommt keinen Cache, die Sprache liegt im UI-Zustand (`core`/`language`).
- **Typen aus der API.** `client/src/shared/api/schema.d.ts` wird von `scripts/gen-api.sh` aus dem OpenAPI-Schema des Servers erzeugt (`npm run gen:api`); `tests/implementation/integration/server/test_openapi_types.py` prüft, dass die Datei dem Schema entspricht (Regel „Typen nie von Hand“).
- **Tests außerhalb von `client/`.** Die Testordner liegen unter `tests/`; damit ihre Importe `react`, `vitest` usw. finden, löst die Vitest-Konfiguration bloße Importe aus Tests wie aus `client/` auf, und `tsconfig.test.json` bildet sie per `paths` auf `client/node_modules` ab.

### Decided

1. **Gerüst**: `client/package.json`, Vite (Proxy `/api` auf 5412), TypeScript, ESLint, Vitest, `scripts/check-next.sh` um den Client erweitern.
2. **ESLint-Regel `architecture/boundaries`** mit ihren Tests an die neuen Pfade anpassen (Schichten `client/src/{app,core,shared,plugins}`, Tests unter `tests/`).
3. **Core kopieren ohne Login** und die kopierten Tests mitnehmen, bis TypeScript, ESLint und Vitest grün sind.
4. **Verbindung und Fehler**: Basis-URL `/api`, Fehlerform `{code, message, details}`, kein Login.
5. **Plugin-Vertrag**: Widget-Beiträge, `slots`, `frame`, `eventHandlers`, Prüfungen in `checkContributions`/`checkSlots`/`checkDefinition`; Tests zuerst.
6. **SSE** (`core/events`) und Verteilung an die Plugins; Test zuerst.
7. **UI-Zustand** (`core.api`, `usePersistentState`), Sprache über den UI-Zustand; Test zuerst.
8. **Start und Layout**: `startApp` ohne Login mit fester Plugin-Liste, `core/settings` mit Slot `core.settings-sections`, Layout-Plugin mit Slots, dunkles Thema, Beispiel-Plugin `example` (nur im Entwicklungsmodus) mit Neuladen bei einem Ereignis.
9. **Typen aus der API**: `gen:api`, `schema.d.ts`, Prüftest.
10. **Integration**: `tsc`, ESLint, Vitest, `vite build` und `scripts/check-next.sh` grün; Techdoku `docs/techdocs/neubau-client.md`.

### Open

- Frage 19 in `STORY-060`.

## 2026-10-16 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant (Details in `docs/techdocs/neubau-client.md`). Abweichungen und Ergänzungen: Die Tabs stehen in der Reihenfolge der Plugin-IDs, der Tab `core/settings` zuletzt (sonst wäre die Einstellungsseite die Startseite); der Kopf zeigt den Namen „ToDo Viewer“ statt eines Logobilds, das es im Neubau nicht gibt; `tests/node_modules` ist ein Verweis auf `client/node_modules`, den `npm install` anlegt (Tests außerhalb von `client/` finden so ihre Pakete, `tsc` und Vitest brauchen keine Sonderregeln); `client/.npmrc` setzt `legacy-peer-deps=true`, weil `npm` 10.9 mit den Peer-Angaben der aktuellen ESLint-Pakete abstürzt (`edgesOut`).
- Abhängigkeiten: die von `ezf-ui` übernommenen (React, React Router, Redux Toolkit, React Redux, i18next und `i18next-browser-languagedetector`, react-i18next, ajv, MUI mit Emotion und `@mui/icons-material`) plus Entwicklungswerkzeuge (Vite, `@vitejs/plugin-react`, TypeScript, ESLint mit `typescript-eslint` und den React-Plugins, Vitest, Testing Library, jsdom, `openapi-typescript`, Typpakete). Nicht übernommen: `ts-command-line-args`.
- Aus dem Backend-Log-Ziel `BackendSink` wurde nichts übernommen (der Neubau hat keine Log-Schnittstelle); Logs gehen an die Konsole. Siehe Frage 20 in `STORY-060`.
- Im Browser geprüft (Chromium, Server auf 5412 mit temporärer Datenbank, Vite-Proxy): Kopfzeile mit Tabs, Seitenleiste, Header-Widget, Beispielseite mit `ok` vom Server; die Sprachwahl landet als `{"language":"de"}` in `core_ui_state`.

### Decided

- Abschlusskriterien geprüft: (1) `client/` baut (`npm run build`) und startet mit Vite-Proxy auf 5412 und zeigt Kopfzeile und Seitenleiste mit dem Beispiel-Plugin; (2) kein Login-Code im Core (`core/auth`, `core/config`, Login-Seite, Keycloak entfernt; Test `does not contain any login`); (3) ein Ereignis vom Server löst im Beispiel-Plugin ein Neuladen aus, ebenso `core.reconnected` nach einer Unterbrechung (`startApp.test.tsx`, `createEventStream.test.ts`); (4) DE/EN umschaltbar, im UI-Zustand des Servers gespeichert (`usePersistentState.test.tsx`, `startApp.test.tsx`, Browser-Lauf); (5) `architecture/boundaries`, `tsc` und Vitest (776 Tests) sind grün.
- `scripts/check-next.sh` (Server und Client) grün; `scripts/check.sh` des alten Viewers grün. Die Typen in `client/src/shared/api/schema.d.ts` sind erzeugt und per `test_openapi_types.py` gegen das Schema geprüft.
- Status: `Awaiting confirmation`.

### Open

- Fragen 19 und 20 in `STORY-060` (Annahmen gelten).
