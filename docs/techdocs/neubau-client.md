# Neubau: Client (`client/`)

Stand des Neubaus (`EPIC-007`); der alte Viewer in `src_old/web/` ist davon unberührt. Verbindliche Regeln:
[Architektur](../development/architecture.md) und Scope `client`. Vorlage des Core: `reference/ezf-ui/` (kopiert und
angepasst, nichts wird von dort importiert).

## Aufbau

```
client/src/
  app/       Composition Root: feste Plugin-Liste, Start, Katalog, Kern-Beiträge
  core/      Plugin-Registry, Slots, Store, Verbindung, Ereignisse, UI-Zustand, Fehler, Banner, Modals, Navigation
  shared/    erzeugte API-Typen (`api/schema.d.ts`), später gemeinsame UI-Bausteine
  plugins/<id>/   plugin.json, index.ts, Seiten, Zustand, API
tests/implementation/unit/client/…   spiegelt client/src/ (Vitest, Testing Library)
tests/helpers/client/                Fakes (Backend, EventSource, UI-Zustand)
```

Schichten und öffentliche API (nur über `index.ts`) prüft die ESLint-Regel `architecture/boundaries`
(`client/configs/eslint/architectureBoundaries.ts`, mit eigenen Tests). Sie kennt auch `src_old/` und `reference/`
(Regel 0: keine Importe von dort).

## Befehle

| Zweck | Befehl |
|---|---|
| Installation | `cd client && npm ci` (legt auch `tests/node_modules` als Verweis auf `client/node_modules` an) |
| Entwicklung | `npm run dev` (Vite, Port 5173; `/api` und `/mcp` gehen an den Server auf 5412) |
| Typen, Regeln, Lint | `npx tsc -b && npm run lint` |
| Tests | `npx vitest run --config configs/vite/vitest.config.ts` |
| Bauen | `npm run build` |
| API-Typen erzeugen | `npm run gen:api` (ruft `scripts/gen-api.sh`: OpenAPI des Servers → `src/shared/api/schema.d.ts`) |

Alles zusammen mit dem Server: `scripts/check-next.sh`. `tests/implementation/integration/server/test_openapi_types.py`
prüft, dass `schema.d.ts` dem Schema des Servers entspricht.

## Start

`startApp` (ohne Login) in fester Reihenfolge: Logging einschalten → auf den Server warten (`GET /api/core/health`; bei
Ausfall ein Banner und erneutes Prüfen, nie ein Abbruch) → Plugins laden (Auswahl aus `app/plugins/activePlugins.ts`, nur
dort steht die feste Liste; `example` nur im Entwicklungsmodus) → Verbindung → Store → Router → Ereignisstrom. Fällt der Server
später aus, startet die Verbindung denselben Test und zeigt das Banner, bis er wieder antwortet.

## Plugin-Vertrag

`plugin.json` (`requires`) und eine `PluginDefinition` aus `index.ts` mit `i18n` (DE, EN), und optional:

| Feld | Bedeutung |
|---|---|
| `contributions` | Beiträge zu Slots: Hauptrouten/Tabs (`core.main`), Seitenleisten-Einträge, **Widgets** `{slot, name, component, order?, when?}` |
| `slots` | die Slots, die das Plugin anbietet (`{ "<name>": { description } }`, Beiträge nutzen `<plugin-id>.<name>`) |
| `reducer`, `api` | eigener Store-Teil unter der Plugin-ID, eigene RTK-Query-API (`createPluginApi`, Cache unter `<id>.api`) |
| `eventHandlers` | `{ "<topic>": (payload, { dispatch, api }) => void }` für Server-Ereignisse; `core.reconnected` nach einem Neuverbinden |
| `frame` | Rahmen um die Routen (Kopfzeile, Seitenleiste); höchstens ein aktives Plugin |

Ein Widget braucht einen Slot, den der Besitzer anbietet und den das beitragende Plugin über `requires` erreicht; der Core
bietet `core.settings-sections` an. `when` nennt die Hauptrouten (`<owner>/<name>`, z. B. `backlog/main`), auf denen das
Widget erscheint; ohne `when` überall. Der Besitzer des Slots zeichnet die Widgets mit `useSlot(slot)` in der festen
Reihenfolge `order`, Plugin-ID, Definition. Die Registry prüft Form, Slot und Besitzer zur Laufzeit; ein fehlerhaftes Plugin
ist `failed`, die abhängigen sind `blocked`, die App läuft weiter.

## Layout

Das Plugin `layout-header-sidebar` liefert den Rahmen: Kopfzeile des Core (Name, Tabs der Hauptrouten, Sprachschalter) mit
den Widgets von `layout-header-sidebar.header-actions` am rechten Ende und links eine Seitenleiste mit den Abschnitten von
`layout-header-sidebar.sidebar-sections`, die zur offenen Hauptroute gehören (`when`); ohne Abschnitt keine Seitenleiste.
Die Tabs stehen in der Reihenfolge der Plugin-IDs, der Tab `core/settings` (Einstellungen) zuletzt; seine Seite
(`core.settings-sections`) zeigt eine Karte je Widget. Das Thema ist fest dunkel in den Farben des alten Viewers
(`core/theme`).

## Server-Ereignisse (SSE)

`core/events`: `EventSource('/api/core/events')` hört auf die Topics, für die ein aktives Plugin einen Handler hat. Bei einem
Fehler wird die Verbindung geschlossen und nach 1, 2, 4 … höchstens 30 Sekunden neu geöffnet; die erste erfolgreiche neue
Verbindung löst `core.reconnected` aus, denn Ereignisse sind nicht garantiert und die Plugins laden neu (üblich:
`dispatch(api.util.invalidateTags([...]))`). Ein Handler, der wirft, wird protokolliert und stoppt die anderen nicht.

## UI-Zustand und Sprache

Dauerhafter UI-Zustand liegt auf dem Server (`GET/PUT /api/core/ui-state/{owner}`, ein JSON-Dokument je Besitzer), nicht im
Browser-Speicher. `usePersistentState(owner, key, default)` → `[Wert, setzen, geladen]`: der Wert gilt sofort überall (Cache
der API `core.api`), das ganze Dokument geht nach 300 ms gesammelt zum Server; vorher wird es geladen, damit ein Schreiben nie
das Dokument des Servers ersetzt. Die Sprache (DE/EN) steht unter `core` / `language`; `LanguageSync` wendet sie nach dem
Laden an und speichert die Wahl des Nutzers. Der Sprachdetektor von i18next hat keinen Cache.

## Fehler und Verbindung

Antworten mit Status ab 500 und fehlende Antworten gelten als „nicht erreichbar“ (Banner, erneuter Test). Alle anderen Fehler
liefert die Verbindung unverändert an den Aufrufer; der Server antwortet mit `{code, message, details}` (siehe
[Neubau: Server](neubau-server.md)), das Frontend übersetzt den `code`. Es gibt keinen Login und keine Cookies.

## Gemeinsame Bausteine (`shared`)

Aus `client/src/shared/index.ts`; keiner hält globalen Store-Zustand, Texte kommen als Eigenschaften (die Plugins
übersetzen; Standardtexte englisch), Test-IDs stehen in `sharedTestIds` (`shared.<element>`).

| Baustein | Zweck |
|---|---|
| `TreeView` + `buildTree` | Baum aus einer flachen Liste (`{id, parentId, label, badge?, statusColor?, progress?}`); die aufgeklappten Knoten und die Auswahl hält der Aufrufer. Tastatur: Pfeile, Pos1/Ende, Enter/Leertaste; Hover-Aktionen (`actions`); Drag & Drop mit `canDrop(source, target, "before" \| "after" \| "inside")` und `onDrop` (ein Knoten lässt sich nie in seinen eigenen Teilbaum ziehen) |
| `ProgressRing` | erledigt/gesamt als Tortendiagramm |
| `DetailPanel`, `DetailSection`, `DetailField` | Kopfleiste mit Icon-Buttons, einklappbare Abschnitte, Felder |
| `InlineField` | Text, Auswahl, Mehrfachauswahl; speichert sofort (Text beim Verlassen oder Enter, Auswahl bei Änderung); ein abgewiesenes Speichern zeigt die Meldung am Feld und behält die Eingabe |
| `EditForm` | Speichern/Abbrechen; bei `version_conflict` ein Hinweis mit „Aktuellen Stand laden“ |
| `MarkdownView`, `MarkdownEditor`, `renderMarkdown` | `marked` + `dompurify`; Editor mit Vorschau daneben; Konflikt mit „Aktuellen Stand anzeigen“ und „Trotzdem speichern“ (`onSave(true)`) |
| `LargeView` | fast vollbildschirmgroße Ansicht mit Inhaltsverzeichnis aus den Überschriften (`extractHeadings`) |
| `FilterSection` | Checkbox-Liste mit Farbpunkt und Zähler für die Seitenleiste |
| `ConfirmDialog`, `ChoiceDialog` | schlichte MUI-Dialoge (siehe Frage 21 in `STORY-060`) |
| `EntityPicker` | Auswahl von Elementen als „Label — Titel“ (einzeln oder mehrfach, mit gesperrten Einträgen) |

Das Beispiel-Plugin hat die Seite „Bausteine“, die Baum, Detailpanel, Inline-Feld und Markdown-Editor zusammen benutzt.

## Plugin `workspace`

`client/src/plugins/workspace/`, benötigt `layout-header-sidebar`. Es hängt zwei Abschnitte in die Seitenleiste (Suche, Projekte) und den Knopf „＋ Neu“ in die Kopfzeile.

- **API** (`workspace.api`, Tag `Projects`): Projekte lesen, anlegen, ändern, ordnen, entfernen und der Ordner-Browser. Das Ereignis `workspace.project.changed` und `core.reconnected` laden die Liste neu.
- **Zustand** (öffentlich, im UI-Zustand des Servers unter dem Besitzer `workspace`): `useSearchText()` (Suchtext), `useProjectSelection()` (`projects`, `visible` = nicht ausgeblendete, `marked` = markiertes Projekt, `toggleVisible`, `mark`). Gespeichert werden `search`, `hidden` (ausgeblendete Projekte, damit ein neues Projekt sofort sichtbar ist) und `marked`.
- **Projekte in der Seitenleiste:** Checkbox blendet ein oder aus, ein Klick markiert (ein zweiter hebt auf), ✎ öffnet die Projektkarte, die Reihenfolge ändert man durch Ziehen. Die Projektkarte (Name, Spiegel-Ordner mit Ordner-Browser, Spiegel an, Auto-Sync, Richtung) legt an, ändert und entfernt; ein Projekt mit Inhalt wird erst nach einer Rückfrage entfernt. Die Sync-Anzeigen (↻, ⚠) kommen mit dem Sync in der Oberfläche.
- **Slot `workspace.create-types`:** Ein Plugin hängt eine Maske für „＋ Neu“ ein. `name` ist der Typ, `component` die Maske, der Titel der Text `create.<name>` im Namensraum des beitragenden Plugins. Die Maske ruft `useCreateDialog()` und bekommt `close()` und `projectUid` (das markierte Projekt, sonst „Allgemein“). „Projekt“ ist immer im Menü.
- **Verknüpfungen:** `LinksSection` (`elementUid`, `readOnly`) zeigt, worauf ein Element verweist und was auf es verweist (mit Rolle; im Papierkorb liegende Gegenstücke durchgestrichen und als „gelöscht“ markiert) und legt neue Verknüpfungen an: Rolle (`Verweis`, `Herkunft`), Ziel über den `EntityPicker`, dessen Treffer der Server liefert (`search_elements`, getippter Text über `onInputChange`). Die Rolle `Auslöser` wird gezeigt, aber hier weder angelegt noch entfernt. Plugins mit Detailpanel bauen den Abschnitt ein (`import { LinksSection } from "../workspace"`); ein Slot dafür entfällt (Frage 24 in `STORY-060`). Das Ereignis `workspace.links.changed` lädt die Verknüpfungen neu.
- **Papierkorb:** Die Hauptroute `workspace/trash` listet die gelöschten Elemente aller Plugins in den sichtbaren Projekten, gefiltert nach dem Suchtext, mit Checkboxen und Sammelaktionen; Wiederherstellen zeigt die Meldung des Plugins, wenn eine Regel es verbietet, endgültiges Löschen fragt vorher. Plugins löschen mit `useDeleteElement()` (`requestDelete(uid, version)`, `dialog`, `failed`): hat das Element Kinder, fragt der Dialog nach und löscht dann mit Kaskade. Das Ereignis `workspace.element.changed` lädt Papierkorb und Verknüpfungen neu. Das Darstellen gelöschter Kinder im Detailpanel (gestrichelt, durchgestrichen) gehört zum Detailpanel des Backlogs.
- **Sync in der Oberfläche** (nutzt die Core-Operationen `sync_status`, `sync_preview`, `sync_execute` und `update_project`): *Stand* eines Projekts (`syncView` in `sync.ts`): „nicht gespiegelt“, „in Sync“, „braucht dich“ (wartende Änderungen oder Konflikte), „pausiert: <Grund>“ (Ordner fehlt, nicht lesbar, Git-Merge-Konflikt, Git-Vorgang, Formatfehler …). In der Projektliste der Seitenleiste steht ⚠ bei „braucht dich“ und „pausiert“ und ↻ bei automatischem Abgleich; Projekte ohne Spiegel werden nicht gefragt. Das Ereignis `core.sync.state` (und `core.reconnected`) lädt den Stand neu. Die Einstellungsseite bekommt den Abschnitt „Projekte“ (`core.settings-sections`): je Projekt eine Karte mit Modus (Aus / Sync von Hand / Sync automatisch), Ordner und Richtung, Stand, letztem Sync und einer Hauptaktion („Spiegel einrichten“ öffnet die Projektkarte, „Abgleichen …“ den Sync-Dialog, bei einer Pause „Prüfen …“); ein Modus ohne Ordner öffnet die Projektkarte. Der **Sync-Dialog** wählt die Richtung, lädt die Vorschau, zeigt zuerst die Konflikte mit dem Feldvergleich (nur abweichende Felder und Verweise, Datenbank | Dateien) und je Konflikt die Wahl Datenbank / Dateien / Später, dazu „Alle: Datenbank“ und „Alle: Dateien“; **Löschungen** (ein Eintrag fehlt auf einer Seite) gehören nie zu „Alle“, die löschende Wahl trifft man einzeln, und nur dann geht `delete_missing` mit. Danach folgen die Übertragungen als Zusammenfassung. Nach dem Ausführen zeigt der Dialog das Ergebnis (Übertragungen, neu angelegte Labels, offene Konflikte); ein veraltetes Token lädt die Vorschau neu, Fehler zeigt er mit der Meldung des Servers (Datei und Zeile bei Formatfehlern).
- Test-IDs: `workspace.<element>` aus `workspaceTestIds`.

## Plugin `backlog`

`client/src/plugins/backlog/`, benötigt `layout-header-sidebar` und `workspace`. Die Hauptroute `backlog/main` zeigt links je sichtbarem Projekt (Projektauswahl und Suchtext kommen aus `workspace`) den Baum Epic → Story → Task mit Fortschrittsring je Item und den Fortschritt des Projekts („Name (erledigt/gesamt)“, Balken), rechts das Detailpanel des gewählten Items. Optionale Kinder sind gestrichelt und gedimmt (`TreeNode.dashed` im gemeinsamen Baum), abgelehnte und optionale zählen nicht im Fortschritt. Die Filter Status und Priorität sind Seitenleisten-Abschnitte nur auf dieser Route (`when: ["backlog/main"]`); sie speichern, was **ausgeblendet** ist, damit neue Werte sichtbar sind. Standard: `Completed` und `Rejected` sind ausgeblendet (zählen aber im Fortschritt). „Epics/Stories zuklappen/aufklappen“ gilt für das markierte Projekt, ohne Markierung für alle gezeigten.

- **API** (`backlog.api`, Tag `Items`): `listItems(projects)` lädt alle Items der gezeigten Projekte; die Filter wirken im Browser (`model.ts`), damit Fortschritt und Zuklappen davon unabhängig bleiben. `getItem(uid)` lädt ein Item. `workspace.element.changed` und `core.reconnected` laden neu.
- **UI-Zustand** (Besitzer `backlog`): `hiddenStatuses`, `hiddenPriorities`, `collapsed` (zugeklappte Items), `selected`.
- **Detailpanel:** Status und Priorität als farbige Marken (übersetzt: Dringend, Wichtig, Normal, Perspektivisch), Bereich, Erstellt, Parent (mit „optional“), Ziel, Fertigstellungskriterien, Kurzfassung und Entscheidung als Markdown, Fortschritt, Abhängigkeiten und Kinder als Verweise (gelöschte durchgestrichen, optionale gestrichelt), Abschnitt „Verknüpfungen“ (`LinksSection` von `workspace`).
- **Bearbeiten:** Im Detailpanel ändern Status, Priorität, Bereich, „Pflicht für Parent“ (nur unter einem Parent) und Abhängigkeiten sofort (`InlineField`, die Meldung des Servers erscheint am Feld). `Completed` und `Rejected` fragen nach einer Entscheidung (Vorschlag auf Englisch wie in den Dateien). „＋ Neuer Bereich …“ fragt nach dem Namen. Die Knöpfe oben: Bearbeiten (Formular mit allen Feldern und Versionskonflikt: „Aktuellen Stand laden“), Kind anlegen (Epic → Story, sonst Task), Typ ändern (danach ein Hinweis mit altem und neuem Label), In den Papierkorb (`useDeleteElement`, fragt bei Kindern). Scheitert ein Schreiben mit `parent_closed`, fragt `useItemWrite` einmal, ob die geschlossenen Vorfahren wieder geöffnet werden sollen, öffnet sie und versucht es erneut.
- **Dokumente:** Der Abschnitt „Dokumente“ im Detailpanel (`DocumentsSection`) listet Notizen und Specs eines Items; ein Klick öffnet das Dokument formatiert (mit Großansicht samt Inhaltsverzeichnis), „Bearbeiten“ öffnet den Editor mit Vorschau; ein Versionskonflikt bietet „Aktuellen Stand zeigen“ und „Trotzdem speichern“ (auf der aktuellen Version). „＋ Notiz-Eintrag“ nimmt Thema und je Abschnitt einen Stichpunkt pro Zeile und fragt beim ersten Eintrag nach der Kurzfassung des Items; „＋ Spec anlegen“ schlägt `<LABEL>_spec.md` vor und öffnet das neue Dokument.
- **Abhängigkeiten-Graph:** Die Hauptroute `backlog/graph` („Abhängigkeiten“) zeigt die Abhängigkeiten als gerichteten Graphen (`@xyflow/react`, Layout mit `elkjs`: „layered“ von links nach rechts, Knoten ohne Abhängigkeiten in der linken Spalte, unabhängige Teilgraphen untereinander). Gezeigt werden nur Items, die an einer sichtbaren Abhängigkeit teilnehmen, gefiltert wie der Baum (Projekte, Status, Priorität, Suche); die Kanten zeigen von der Abhängigkeit zum Abhängigen. Auswahl (dieselbe wie im Baum), Hover und ⌘/Strg/⇧-Klick heben Knoten, Kanten und direkte Nachbarn hervor, der Rest wird abgedunkelt; ein zweiter Klick auf den gewählten Knoten, ein Klick auf den Hintergrund und Esc setzen zurück. Die reinen Funktionen stehen in `graphModel.ts` (`dependencyGraph`, `connectedComponents`, `focusNeighborhood`, `highlight`), das Layout in `graphLayout.ts`. Die Seite ist ein Lazy-Import der Hauptroute und `elkjs` wird erst beim ersten Layout geladen: beide stehen im Build in eigenen Teilen (`GraphPage-*.js`, `elk.bundled-*.js`).
- **Neu-Dialog:** Epic, Story und Task hängen als `workspace.create-types` im Menü „＋ Neu“ (`create.epic` … im Namensraum `backlog`); das Formular legt im markierten Projekt an.
- **Drag & Drop** im Baum: auf ein Item (hinein, ans Ende), davor oder danach; `placementOf` rechnet Parent und Stelle (unter den Geschwistern ohne das gezogene Item) und verbietet, was die Struktur verbietet (Epic nur als Wurzel, kein Kind unter einem Task); alles Weitere prüft der Server und die Meldung steht über dem Baum.
- Test-IDs: `backlog.<element>` aus `backlogTestIds`.
