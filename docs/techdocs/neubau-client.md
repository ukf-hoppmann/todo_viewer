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
| Entwicklung | `npm run dev` (Vite, Port 5173; `/api` und `/mcp` gehen an den Server auf 5411) |
| Typen, Regeln, Lint | `npx tsc -b && npm run lint` |
| Tests | `npx vitest run --config configs/vite/vitest.config.ts` |
| Bauen | `npm run build` |
| API-Typen erzeugen | `npm run gen:api` (ruft `scripts/gen-api.sh`: OpenAPI des Servers → `src/shared/api/schema.d.ts`) |

Alles zusammen mit dem Server: `scripts/check-next.sh`. `tests/implementation/integration/server/test_openapi_types.py`
prüft, dass `schema.d.ts` dem Schema des Servers entspricht.

## Start

`startApp` (ohne Login) in fester Reihenfolge: Logging einschalten (neben der Konsole der `BackendSink`, der Warnungen und
Fehler einzeln an `POST /api/core/client-log` sendet, ohne Wiederholung; schlägt das Senden fehl, steht nur eine
`console.warn`-Zeile, nie ein neuer Logeintrag) → auf den Server warten (`GET /api/core/health`; bei
Ausfall ein Banner und erneutes Prüfen, nie ein Abbruch) → Plugins laden (Auswahl aus `app/plugins/activePlugins.ts`, nur
dort steht die feste Liste; `example` nur im Entwicklungsmodus) → Verbindung → Store → Router → Ereignisstrom. Fällt der Server
später aus, startet die Verbindung denselben Test und zeigt das Banner, bis er wieder antwortet.

## Plugin-Vertrag

`plugin.json` (`requires`) und eine `PluginDefinition` aus `index.ts` mit `i18n` (DE, EN), und optional:

| Feld | Bedeutung |
|---|---|
| `contributions` | Beiträge zu Slots: Hauptrouten/Tabs (`core.main`, mit `page` und `layout`) und **Widgets** `{slot, name, component, order?, when?}` |
| `slots` | die Slots, die das Plugin anbietet (`{ "<name>": { description } }`, Beiträge nutzen `<plugin-id>.<name>`) |
| `reducer`, `api` | eigener Store-Teil unter der Plugin-ID, eigene RTK-Query-API (`createPluginApi`, Cache unter `<id>.api`) |
| `eventHandlers` | `{ "<topic>": (payload, { dispatch, api }) => void }` für Server-Ereignisse; `core.reconnected` nach einem Neuverbinden |
| `frame` | Rahmen um die Routen (Kopfzeile); höchstens ein aktives Plugin |

Ein Widget braucht einen Slot, den der Besitzer anbietet und den das beitragende Plugin über `requires` erreicht; der Core
bietet `core.settings-sections` und `core.sidebar-sections` an. `when` nennt die Hauptrouten (`<owner>/<name>`, z. B. `backlog/main`), auf denen das
Widget erscheint; ohne `when` überall. `group` gilt nur im Slot `core.settings-sections` (siehe unten). Der Besitzer des Slots zeichnet die Widgets mit `useSlot(slot)` in der festen
Reihenfolge `order`, Plugin-ID, Definition. Die Registry prüft Form, Slot und Besitzer zur Laufzeit; ein fehlerhaftes Plugin
ist `failed`, die abhängigen sind `blocked`, die App läuft weiter.

## Layout

Das Plugin `layout-header-sidebar` liefert den Rahmen: Kopfzeile des Core (Name, Tabs der Hauptrouten, Sprachschalter) mit
den Widgets von `layout-header-sidebar.header-actions` am rechten Ende.

Darunter steht für jede Hauptroute das Seitengerüst des Core (`core/navigation/SubLayout`). Die Route schaltet seine
Bereiche mit `layout: { header?, sidebar?, detail? }` ein (Standard aus); es sind leere Gerüste, gefüllt von den Plugins:

| Bereich | Füllung |
|---|---|
| `header` (oben) | die Seite mit `usePageHeader(inhalt)` |
| `sidebar` (links, 260 px) | die Abschnitte von `core.sidebar-sections`, die zur offenen Hauptroute gehören (`when`); ohne Abschnitt keine Seitenleiste |
| `detail` (rechts, halbe Breite) | die Seite mit `usePageDetail(inhalt)`; `undefined`, `null`, `false` oder `""` blenden die Spalte aus. Fehler im Inhalt bleiben in der Spalte (eigene Fehlergrenze), den Schließen-Knopf bringt der Inhalt mit (`DetailPanel`) |

Backlog, Abhängigkeiten, Memos, Wecker und Papierkorb nutzen `sidebar` und `detail`; keine Seite baut ihre Aufteilung selbst.
Die Tabs stehen in der Reihenfolge der Plugin-IDs, der Tab `core/settings` (Einstellungen) zuletzt; seine Seite
(`core.settings-sections`) zeigt links eine Navigation der Gruppen und rechts eine Karte je Widget der offenen Gruppe. Die Gruppen sind fest im Core: `projects` („Projekte“, alles Projektspezifische) und `system` („System“: Memos, Wecker, später Auto-Sync); ein Widget wählt seine Gruppe mit `group`, ohne Angabe oder mit unbekanntem Wert landet es in `system`. Die offene Gruppe steht in der URL (`/core/settings?group=system`); ohne gültigen Wert öffnet die erste Gruppe mit Abschnitten. Das Thema ist fest dunkel in den Farben des alten Viewers
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
| `TreeView` + `buildTree` | Baum aus einer flachen Liste (`{id, parentId, label, badge?, statusColor?, progress?, dashed?, count?, tag?, tagColor?, area?}`; `count` ist eine Zahl am rechten Rand, `tag` ein kleines Wort vor dem Titel, `area` 1 oder 2 hinterlegt die Zeile als Bereich, `dashed` macht die Führungslinie des Knotens samt Teilbaum gestrichelt, den Titel gedimmt und den Statuspunkt hohl); links jeder Zeile steht je Ebene darüber eine senkrechte Führungslinie (`guideLines`); die aufgeklappten Knoten und die Auswahl hält der Aufrufer. Tastatur: Pfeile, Pos1/Ende, Enter/Leertaste; Hover-Aktionen (`actions`); `trailing` zeigt etwas rechts neben dem Titel, solange Zeiger oder Fokus auf der Zeile stehen (wie `actions`, z. B. ein Symbol mit Tooltip); Drag & Drop mit `canDrop(source, target, "before" \| "after" \| "inside")` und `onDrop` (ein Knoten lässt sich nie in seinen eigenen Teilbaum ziehen); jede Zeile ist einzeln gemerkt (`memo`), damit ein Klick nur die Zeile mit der alten und die mit der neuen Auswahl neu zeichnet – dafür müssen `nodes`, `expanded`, `trailing` und `actions` zwischen den Renderings dieselben Objekte bleiben (`useMemo`/`useCallback`); die Handler (`onSelect`, `onToggle`, `canDrop`, `onDrop`) dürfen jedes Mal neu sein |
| `ProgressRing` | erledigt/gesamt als Tortendiagramm |
| `DetailPanel`, `DetailSection`, `DetailField` | Kopfleiste mit Icon-Buttons, einklappbare Abschnitte, Felder |
| `InlineField` | Text, Auswahl, Mehrfachauswahl; speichert sofort (Text beim Verlassen oder Enter, Auswahl bei Änderung); ein abgewiesenes Speichern zeigt die Meldung am Feld und behält die Eingabe |
| `EditForm` | Speichern/Abbrechen; bei `version_conflict` ein Hinweis mit „Aktuellen Stand laden“ |
| `MarkdownView`, `MarkdownEditor`, `renderMarkdown` | `marked` + `dompurify`; Editor mit Vorschau daneben; Konflikt mit „Aktuellen Stand anzeigen“ und „Trotzdem speichern“ (`onSave(true)`) |
| `LargeView` | fast vollbildschirmgroße Ansicht mit Inhaltsverzeichnis aus den Überschriften (`extractHeadings`) |
| `FilterSection` | Checkbox-Liste mit Farbpunkt und Zähler für die Seitenleiste |
| `ConfirmDialog`, `ChoiceDialog` | schlichte MUI-Dialoge (siehe Frage 21 in `STORY-060`) |
| `EntityPicker` | Auswahl von Elementen als „Label — Titel“ (einzeln oder mehrfach, mit gesperrten Einträgen) |
| `IconAction` | Aktion als Icon mit Tooltip, der zugleich der zugängliche Name ist (`label`, `icon`, `onClick`, `disabled`, `size`, `color`, `testId`) |
| `DocumentsSection` | Abschnitt „Dokumente“ eines Detailpanels: Liste der Notizen und Specs, „Notiz-Eintrag anlegen“ und „Spec anlegen“ als Icons; der Dokument-Dialog hat Großansicht, Bearbeiten und Schließen als Icons in der Titelzeile, beim Bearbeiten den `MarkdownEditor` und unten „Abbrechen“. Der Besitzer reicht die Daten herein: `owner`, `names`, `readOnly`, `spec` (Vorschlag für Name und erste Zeile), `summary` (nur gesetzt, wenn der Eintrag nach der Kurzfassung fragen soll), `useDocument(owner, name)` (sein Query-Hook), `saveDocument`, `appendEntry`, optional `deleteDocument(name, version)` (nur dann hat der Dialog ein Symbol „In den Papierkorb legen“ mit Rückfrage; bei Fehlern erscheint die Meldung im Dialog), `errorMessage` und `labels` |

Regel für Knöpfe: häufige, bekannte Aktionen in Kopf- und Werkzeugleisten und in Listenzeilen sind `IconAction`s, sofern das Icon für sich spricht (Zuklappen ist darum ein schmaler Textknopf); Dialog-Fußzeilen (Abbrechen, Speichern, Bestätigen), fachliche Entscheidungen (z. B. die Hinweis-Entscheidungen, „Alle: Datenbank“), Fehler- und Konfliktaktionen und Einmal-Aktionen („Spiegel einrichten“, „Benachrichtigungen aktivieren“) bleiben Text; die Hauptaktion einer Seite und Unumkehrbares tragen Icon und Text.

Das Beispiel-Plugin hat die Seite „Bausteine“, die Baum, Detailpanel, Inline-Feld und Markdown-Editor zusammen benutzt.

## Plugin `workspace`

`client/src/plugins/workspace/`, benötigt `layout-header-sidebar`. Es hängt zwei Abschnitte in die Seitenleiste (Suche, Projekte) und den Knopf „＋ Neu“ in die Kopfzeile.

- **API** (`workspace.api`, Tag `Projects`): Projekte lesen, anlegen, ändern, ordnen, entfernen und der Ordner-Browser. Das Ereignis `workspace.project.changed` und `core.reconnected` laden die Liste neu.
- **Zustand** (öffentlich, im UI-Zustand des Servers unter dem Besitzer `workspace`): `useSearchText()` (Suchtext), `useProjectSelection()` (`projects`, `visible` = nicht ausgeblendete, `marked` = markiertes Projekt, `toggleVisible`, `mark`). Gespeichert werden `search`, `hidden` (ausgeblendete Projekte, damit ein neues Projekt sofort sichtbar ist) und `marked`.
- **Projekte in der Seitenleiste:** Checkbox blendet ein oder aus, ein Klick markiert (ein zweiter hebt auf), die Reihenfolge ändert man durch Ziehen. Im Kopf stehen Glocke, ✎ und ＋: ✎ öffnet die Projektkarte des markierten Projekts (ohne Markierung ausgegraut mit dem Hinweis „Erst ein Projekt auswählen“), ebenso ein Doppelklick auf den Namen; eine Zeile hat keinen eigenen Stift. Die Projektkarte (Name, Spiegel-Ordner mit Ordner-Browser, Spiegel an, Auto-Sync, Richtung) legt an, ändert und entfernt; ein Projekt mit Inhalt wird erst nach einer Rückfrage entfernt. Die Sync-Anzeigen (↻, ⚠) kommen mit dem Sync in der Oberfläche.
- **Glocke (Fälliges):** Die Glocke im Kopf der Projekte zählt alles Fällige aller Projekte (auch ausgeblendeter) und setzt die Zahl als „(n) …“ vor den Titel des Browser-Tabs; jede Projektzeile mit Fälligem hat eine eigene Glocke mit der Zahl dieses Projekts. Ohne Fälliges erscheint keine Glocke. Ein Klick öffnet immer eine Liste (`AttentionList`), auch bei einem Eintrag: Wecker und Notes gemischt, das zuletzt fällig Gewordene oben und aufgeklappt (Untertitel und Aktionen), die übrigen zugeklappt; ein Klick auf den Titel springt zum Element und schließt die Liste. Die Einträge liefern die Plugins über den **Slot `workspace.attention-sources`**: ein Beitrag ist eine Komponente ohne Ausgabe, die ihre Einträge mit `useReportAttention(entries)` meldet (`AttentionEntry`: `key` = `<Besitzer>:<uid>`, `projectUid`, `dueSince` (ISO), Art-Icon, `title`, `caption`, `actions` – mit Icon als Icon-Knopf, ohne als kleiner Textknopf –, `open()`). `AttentionProvider` in `ProjectsSection` zeichnet die Quellen und sammelt ihre Einträge; Sortieren und Filtern sind reine Funktionen in `attention.ts`. Die Daten bleiben in der API des beitragenden Plugins.
- **Slot `workspace.create-types`:** Ein Plugin hängt eine Maske für „＋ Neu“ ein. `name` ist der Typ, `component` die Maske, der Titel der Text `create.<name>` im Namensraum des beitragenden Plugins. Die Maske ruft `useCreateDialog()` und bekommt `close()` und `projectUid` (das markierte Projekt, sonst „Allgemein“). „Projekt“ ist immer im Menü.
- **Verknüpfungen:** `LinksSection` (`elementUid`, `readOnly`) zeigt, worauf ein Element verweist und was auf es verweist (mit Rolle; im Papierkorb liegende Gegenstücke durchgestrichen und als „gelöscht“ markiert) und legt neue Verknüpfungen an: Rolle (`Verweis`, `Herkunft`), Ziel über den `EntityPicker`, dessen Treffer der Server liefert (`search_elements`, getippter Text über `onInputChange`). Die Rolle `Auslöser` wird gezeigt, aber hier weder angelegt noch entfernt. Plugins mit Detailpanel bauen den Abschnitt ein (`import { LinksSection } from "../workspace"`); ein Slot dafür entfällt (Frage 24 in `STORY-060`). Das Ereignis `workspace.links.changed` lädt die Verknüpfungen neu.
- **Slot `workspace.element-detail` und `ElementDetail`:** Ein Plugin zeigt ein Element eines anderen Plugins, ohne es zu benötigen: `ElementDetail({uid, kind, label?, title?, onClose?, onSelect?})` zeichnet die Ansicht, die der Besitzer der Art eingehängt hat (`name` des Widgets = Elementart; `useShownElement()` liefert ihr das Element). `backlog` hängt `ItemDetail` für `epic`, `story`, `task` ein, `notes` `NoteDetail` für `note` (beide als Lazy-Import). Ohne eingehängte Ansicht (z. B. `topic`) zeigt `ElementDetail` Label, Titel und die Verknüpfungen nur lesend.
- **Papierkorb:** Die Hauptroute `workspace/trash` listet die gelöschten Elemente aller Plugins in den sichtbaren Projekten, gefiltert nach dem Suchtext, mit Checkboxen und Sammelaktionen; gelöschte Dokumente von Items stehen als Zeilen mit Dokument-Symbol dazwischen (Label des Items, Name des Dokuments); ein Klick auf eine Zeile zeigt das Element in der Detailspalte (`ElementDetail`; bei einem Dokument das Item, zu dem es gehörte), Checkbox und Knöpfe der Zeile öffnen es nicht; Wiederherstellen zeigt die Meldung des Plugins, wenn eine Regel es verbietet, endgültiges Löschen fragt vorher. Plugins löschen mit `useDeleteElement()` (`requestDelete(uid, version)`, `dialog`, `failed`): hat das Element Kinder, fragt der Dialog nach und löscht dann mit Kaskade. Das Ereignis `workspace.element.changed` lädt Papierkorb und Verknüpfungen neu. Das Darstellen gelöschter Kinder im Detailpanel (gestrichelt, durchgestrichen) gehört zum Detailpanel des Backlogs.
- **Sync in der Oberfläche** (nutzt die Core-Operationen `sync_status`, `sync_preview`, `sync_execute` und `update_project`): *Stand* eines Projekts (`syncView` in `sync.ts`): „nicht gespiegelt“, „in Sync“, „braucht dich“ (wartende Änderungen oder Konflikte), „pausiert: <Grund>“ (Ordner fehlt, nicht lesbar, Git-Merge-Konflikt, Git-Vorgang, Formatfehler …). In der Projektliste der Seitenleiste steht ⚠ bei „braucht dich“ und „pausiert“ (ein Knopf, der den Sync-Dialog des Projekts öffnet) und ein ↻-Knopf bei jedem gespiegelten Projekt (nur, solange die Zeile unter der Maus liegt oder den Fokus hat), der ebenfalls den Sync-Dialog mit der Vorschau öffnet (Tooltip „Abgleichen …“, bei Auto-Sync mit Zusatz); Projekte ohne Spiegel werden nicht gefragt und haben keinen Knopf. Das Ereignis `core.sync.state` (und `core.reconnected`) lädt den Stand neu. Die Einstellungsseite bekommt den Abschnitt „Projekte“ (`core.settings-sections`): je Projekt eine kompakte Zeile in einer gemeinsamen Karte: Name, Stand, Modus (Aus / Sync von Hand / Sync automatisch) und drei Icons mit Tooltip: „Projekt bearbeiten“, die Hauptaktion („Spiegel einrichten“ mit Link-Icon öffnet die Projektkarte, „Abgleichen …“ mit Sync-Icon den Sync-Dialog, bei einer Pause „Prüfen …“ mit Warn-Icon) und „Details“ (Pfeil). Ordner und Richtung sowie der letzte Sync stehen im Detail, das zunächst eingeklappt ist (nur lokaler Zustand, nicht gespeichert); ein Modus ohne Ordner öffnet die Projektkarte. Die Gruppe „System“ bekommt vom Plugin den Abschnitt „Auto-Sync“ (`AutoSyncSettings`, Slot `core.settings-sections`, `group: "system"`): ein Zahlenfeld für den Takt in Sekunden (`GET/PUT core/settings/sync`, `0` = aus), das ohne Neustart wirkt; setzt die Umgebung `AUTO_SYNC_INTERVAL`, ist Feld und Knopf gesperrt und ein Hinweis nennt den Grund. Das Ereignis `core.settings.changed` (und `core.reconnected`) lädt den Wert neu. Der **Sync-Dialog** wählt die Richtung, lädt die Vorschau, zeigt zuerst die Konflikte mit dem Feldvergleich (nur abweichende Felder und Verweise, Datenbank | Dateien) und je Konflikt die Wahl Datenbank / Dateien / Später, dazu „Alle: Datenbank“ und „Alle: Dateien“; **Löschungen** (ein Eintrag fehlt auf einer Seite) gehören nie zu „Alle“, die löschende Wahl trifft man einzeln, und nur dann geht `delete_missing` mit. Danach folgen die Übertragungen als Zusammenfassung. Nach dem Ausführen zeigt der Dialog das Ergebnis (Übertragungen, neu angelegte Labels, offene Konflikte) und lädt die Vorschau neu, sodass entschiedene Konflikte verschwinden; ein veraltetes Token lädt die Vorschau neu, Fehler zeigt er mit der Meldung des Servers (Datei und Zeile bei Formatfehlern).
- Test-IDs: `workspace.<element>` aus `workspaceTestIds`.

## Plugin `backlog`

`client/src/plugins/backlog/`, benötigt `layout-header-sidebar` und `workspace`. Die Hauptroute `backlog/main` zeigt links je sichtbarem Projekt (Projektauswahl und Suchtext kommen aus `workspace`) den Baum Epic → Story → Task mit Fortschrittsring je Item und den Fortschritt des Projekts („Name (erledigt/gesamt)“, Balken), in der Detailspalte das Detailpanel des gewählten Items. Optionale Kinder (nicht Pflicht für den Parent) haben eine gestrichelte Führungslinie, einen gedimmten Titel und einen hohlen Statuspunkt (`TreeNode.dashed` im gemeinsamen Baum), abgelehnte und optionale zählen nicht im Fortschritt. Die Filter Status und Priorität sind Seitenleisten-Abschnitte nur auf dieser Route und dem Graphen (`when: ["backlog/main", "backlog/graph"]`); sie speichern, was **ausgeblendet** ist, damit neue Werte sichtbar sind. Standard: `Completed` und `Rejected` sind ausgeblendet (zählen aber im Fortschritt). „Epics/Stories zuklappen/aufklappen“ (schmale Textknöpfe über dem Baum) gilt für das markierte Projekt, ohne Markierung für alle gezeigten. Daneben „Erweiterte Markierung“ (Standard an): ein Root-Item samt Inhalt ist hell hinterlegt und blau gekantet, eine Story unter einem Epic samt Tasks grau gekantet.

- **API** (`backlog.api`, Tag `Items`): `listItems(projects)` lädt alle Items der gezeigten Projekte; die Filter wirken im Browser (`model.ts`), damit Fortschritt und Zuklappen davon unabhängig bleiben. `getItem(uid)` lädt ein Item. `backlog.item.changed`, `workspace.element.changed` und `core.reconnected` laden neu, ebenso `core.sync.state` (mit `Documents`): ein Sync übernimmt Einträge aus den Dateien, ohne `backlog.*.changed` zu melden.
- **UI-Zustand** (Besitzer `backlog`): `hiddenStatuses`, `hiddenPriorities`, `collapsed` (zugeklappte Items), `selected`, `extendedMarking`.
- **Detailpanel:** Status und Priorität als farbige Marken (übersetzt: Dringend, Wichtig, Normal, Perspektivisch), Bereich, Erstellt, Parent (mit „optional“), Ziel, Fertigstellungskriterien, Kurzfassung und Entscheidung als Markdown, Fortschritt, Abhängigkeiten und Kinder als Verweise (gelöschte durchgestrichen, optionale gestrichelt), Abschnitt „Verknüpfungen“ (`LinksSection` von `workspace`).
- **Bearbeiten:** Im Detailpanel ändern Status, Priorität, Bereich, „Pflicht für Parent“ (nur unter einem Parent) und Abhängigkeiten sofort (`InlineField`, die Meldung des Servers erscheint am Feld). `Completed` und `Rejected` fragen nach einer Entscheidung (Vorschlag auf Englisch wie in den Dateien). „＋ Neuer Bereich …“ fragt nach dem Namen. Die Knöpfe oben: Bearbeiten (Formular mit allen Feldern und Versionskonflikt: „Aktuellen Stand laden“), Kind anlegen (Epic → Story, sonst Task), Typ ändern (danach ein Hinweis mit altem und neuem Label), In den Papierkorb (`useDeleteElement`, fragt bei Kindern). Scheitert ein Schreiben mit `parent_closed`, fragt `useItemWrite` einmal, ob die geschlossenen Vorfahren wieder geöffnet werden sollen, öffnet sie und versucht es erneut.
- **Dokumente:** Der Abschnitt „Dokumente“ im Detailpanel (`DocumentsSection`) listet Notizen und Specs eines Items; ein Klick öffnet das Dokument formatiert (mit Großansicht samt Inhaltsverzeichnis), „Bearbeiten“ öffnet den Editor mit Vorschau; ein Versionskonflikt bietet „Aktuellen Stand zeigen“ und „Trotzdem speichern“ (auf der aktuellen Version). „Notiz-Eintrag anlegen“ nimmt Thema und je Abschnitt einen Stichpunkt pro Zeile und fragt beim ersten Eintrag nach der Kurzfassung des Items; „Spec anlegen“ schlägt `<LABEL>_spec.md` vor und öffnet das neue Dokument. Im Dokument-Dialog legt das Papierkorb-Symbol (mit Rückfrage; bei der Notiz mit dem Hinweis, dass die Kurzfassung mitgeht) das Dokument in der gezeigten Version in den Papierkorb und schließt den Dialog; bei einem Item im Papierkorb gibt es das Symbol nicht. Der Abschnitt ist der gemeinsame Baustein `DocumentsSection` aus `shared`; `backlog` reicht Item, Hooks und Texte herein.
- **Stand der Notizen (STORY-093, TASK-045):** Hat ein Item Notizen, steht im Abschnitt „Dokumente“ oberhalb der Dateiliste der Kopf (`NotesHead`, Überschrift „Stand“, Markdown aus `GET …/notes/state`) und darunter ein Knopf „Protokoll“, der die Protokolleinträge (`GET …/notes/entries`, neuester zuerst, mit Datum und Thema) auf- und zuklappt; sie werden erst beim Aufklappen geladen. Ist der Kopf `stale` oder `missing`, steht neben der Überschrift ein Warnsymbol mit Tooltip; ohne Kopf steht „Noch kein Stand eingetragen.“. Items ohne Notizen zeigen nichts. In der Liste (Baum) trägt jedes Item mit Notizen (`notes_state` des Index nicht leer) ein kleines Notizsymbol (`NotesPeek` über `TreeView.trailing`), das erst beim Darüberfahren über die Zeile erscheint: grau bei `current`, gedimmt bei `missing` (der Normalfall älterer Notizen), Warnfarbe bei `stale`. Fährt man darüber, zeigt ein Tooltip auf eigenem Hintergrund den Kopf; er wird erst beim ersten Hover geladen. Die Darstellung (`HeadSections`, Zerlegung in der reinen Funktion `parseHead`) setzt jeden Schlüssel (`Goal/Status`, `Next step`, `Open`, `Decided`, `References`) übersetzt in Akzentfarbe und Großbuchstaben ab (Namensraum `backlog`, `notes.key.*`), zeigt den Text darunter und Unterpunkte als Liste, ein Datum in Klammern am Ende gedimmt; dieselbe Darstellung hat der Kopf in der Detailansicht. Text, der nicht die Form `- Schlüssel: Text` hat, erscheint unverändert. Das Protokoll gibt es nur in der Detailansicht. Neuladen läuft über die Tags `Items` und `Documents` nach `backlog.document.changed`. Texte: Namensraum `backlog`, Schlüssel `notes.*`; Test-IDs `backlog.notes-*` (`notesPeek`, `notesHead`, `notesHeadContent`, `notesHeadWarning`, `notesLogToggle`, `notesLogEntry`).
- **Abhängigkeiten-Graph:** Die Hauptroute `backlog/graph` („Abhängigkeiten“) zeigt die Abhängigkeiten als gerichteten Graphen (`@xyflow/react`, Layout mit `elkjs`: „layered“ von links nach rechts, Knoten ohne Abhängigkeiten in der linken Spalte, unabhängige Teilgraphen untereinander). Gezeigt werden nur Items, die an einer sichtbaren Abhängigkeit teilnehmen, gefiltert wie der Baum (Projekte, Status, Priorität, Suche); die Kanten zeigen von der Abhängigkeit zum Abhängigen. Auswahl (dieselbe wie im Baum), Hover und ⌘/Strg/⇧-Klick heben Knoten, Kanten und direkte Nachbarn hervor, der Rest wird abgedunkelt; ein zweiter Klick auf den gewählten Knoten, ein Klick auf den Hintergrund und Esc setzen zurück. Die reinen Funktionen stehen in `graphModel.ts` (`dependencyGraph`, `connectedComponents`, `focusNeighborhood`, `highlight`), das Layout in `graphLayout.ts`. Die Seite ist ein Lazy-Import der Hauptroute und `elkjs` wird erst beim ersten Layout geladen: beide stehen im Build in eigenen Teilen (`GraphPage-*.js`, `elk.bundled-*.js`).
- **Neu-Dialog:** Epic, Story und Task hängen als `workspace.create-types` im Menü „＋ Neu“ (`create.epic` … im Namensraum `backlog`); das Formular legt im markierten Projekt an.
- **Drag & Drop** im Baum: auf ein Item (hinein, ans Ende), davor oder danach; `placementOf` rechnet Parent und Stelle (unter den Geschwistern ohne das gezogene Item) und verbietet, was die Struktur verbietet (Epic nur als Wurzel, kein Kind unter einem Task); alles Weitere prüft der Server und die Meldung steht über dem Baum.
- Test-IDs: `backlog.<element>` aus `backlogTestIds`; die des Dokumente-Abschnitts stehen in `sharedTestIds`.

## Plugin `memos`

`client/src/plugins/memos/`, benötigt `layout-header-sidebar`, `workspace` und `backlog`. Die Hauptroute `memos/main` zeigt links je sichtbarem Projekt den Baum Topic → Unter-Topic → Memo (Memos ohne Topic stehen direkt am Projekt) und in der Detailspalte das Detail der gewählten Memo. Der Baum benutzt den gemeinsamen `TreeView` mit den Feldern `tag` („Topic“/„Memo“), `count` (Zahl der gezeigten Memos samt Unter-Topics) und `area` (Hervorhebung): mit der gespeicherten Checkbox „Erweiterte Markierung“ (Standard an) ist der Bereich eines Topics der ersten Ebene samt Inhalt hell hinterlegt und blau gekantet, der eines Topics der zweiten (und tieferer) Ebene grau gekantet. Je Ebene stehen Topics mit fälligen Memos zuerst, Topics vor Memos, dann nach Label. Archivierte Topics samt Inhalt sind ausgeblendet (Eintrag „Archivierte Topics“ unten im Status-Abschnitt der Seitenleiste zeigt sie), leere Topics bleiben sichtbar, bei einer Suche bleiben die Treffer, die Topics auf ihrem Weg und Topics mit passendem Namen (alles aufgeklappt).

- **API** (`memos.api`, Tags `Memos`, `Due`, `Documents`, `Settings`): `listIndex(projects)` lädt Topics und alle Memos der gezeigten Projekte; Status-Filter und Suche wirken im Browser (`model.ts`), damit Zähler und Zuklappen davon unabhängig bleiben. Die Ereignisse `memos.*`, `workspace.element.changed` und `core.reconnected` laden neu.
- **UI-Zustand** (Besitzer `memos`): `shownStatuses` (Standard: wartet, fällig, zurückgestellt), `collapsed`, `selected`, `extendedMarking`, `showArchivedTopics`. Die Status-Auswahl (samt „Archivierte Topics“) ist ein Seitenleisten-Abschnitt nur auf `memos/main`; über dem Baum stehen nur „Topics zuklappen/aufklappen“ und „Erweiterte Markierung“.
- **Detail** (`MemoDetail`): Aktionsleiste Bearbeiten, Erledigen, Verwerfen, Zurückstellen (Dialog mit Datum), Behalten, Löschen (Papierkorb über `useDeleteElement`), Großansicht; für ein archiviertes Memo Zurückholen, Großansicht, Löschen. Darunter Status (auch „mit dem Topic archiviert“), Topic-Pfad, Prüf-Datum, Langtext und die Abschnitte Dokumente und Verknüpfungen (`LinksSection`). Fehler des Servers stehen als Meldung über dem Detail.
- **Topics.** Die Aktionen eines Topics erscheinen beim Überfahren der Zeile: neues Memo darin, Unter-Topic, Umbenennen/Termin, Verschieben (Auswahl des Parents), Archivieren, Löschen; ein archiviertes Topic bietet „Wieder aktivieren“. Archivieren und Löschen öffnen denselben Dialog: ein leeres Topic wird mit OK sofort behandelt, bei Inhalt nennt er die Zahlen und bietet die Wahl „Archivierte Memos behalten“ und „Aktive Memos verschieben“ (mit Zieltopic); alles geht in einer Anfrage, Abbrechen ändert nichts. Das neutrale Topic „Archiviert“ hat nur „Neue Memo“ und „Unter-Topic“.
- **Drag & Drop** (HTML5, über den `TreeView`; reine Regel `dropChange`): ein Memo oder ein Topic lässt sich in ein Topic ziehen (darin) oder neben einen Knoten (unter dessen Topic bzw. Parent); auf den Namen des Projekts gezogen verliert sie das Topic (ein Topic wird Wurzel). Nicht erlaubt: anderes Projekt, in ein archiviertes Topic, ein Memo als Behälter, in den eigenen Teilbaum, das Topic „Archiviert“ verschieben, und was nichts ändert. Die Tiefe prüft der Server; seine Meldung steht über dem Baum.
- **Auslöser und Hinweise** (Detail des Memos): Abschnitt „Auslöser“ (Liste mit „eingetreten“/„schon erreicht“, Entfernen, „Auslöser hinzufügen“ (Icon) mit Art, Item-Suche über `workspace` und Status), Abschnitt „Hinweise“ (Text je Ursache, ein Knopf je Entscheidung; „Befördern …“ öffnet den Dialog), Zeile „Fällig wegen“. Die Aktion „Zu Item befördern …“ der Leiste öffnet denselben Dialog (`PromoteDialog`: Typ, Titel, Bereich, Ziel, Kriterien; die Meldung des Backlogs bleibt im Dialog).
- **Fällig-Liste:** der Klick auf den Zähler zeigt die fälligen Memos gruppiert nach Grund (Auslöser, Hinweis, Termin, Prüfung) mit Topic-Pfad und den Aktionen je Memo (Behalten, Zurückstellen, Erledigen, Verwerfen; bei einem Hinweis stattdessen seine Entscheidungen außer „Befördern“).
- **Slot `backlog.item-detail`** (von `backlog` angeboten, Widgets ohne Eigenschaften; `useItemDetail()` liefert das Item): `memos` hängt dort die offenen Hinweise an das Item (quittieren) und „Zum Memo zurückstufen“ (nur bei `Open`, nicht gelöscht) ein.
- **Fällige Memos** (`MemosAttention`, Slot `workspace.attention-sources`): melden sich in der Glocke der Projekte, sortiert nach `due_since` des Servers (sonst Prüfdatum), mit dem Grund (Auslöser, Hinweis, Termin, Prüfung) und dem Topic-Pfad als Untertitel und den Aktionen Behalten, Zurückstellen, Erledigt, Verworfen bzw. den Entscheidungen des Hinweises (ohne Befördern). Die Wahl blendet das Projekt bei Bedarf ein, merkt das Memo als gewählte und öffnet `memos/main`. Die Liste lädt nur auf Ereignisse neu (`memos.*`, auch `memos.due`, wenn ein Prüfdatum oder Topic-Termin erreicht ist); die Quelle fragt nicht selbst nach.
- **Einstellungen** (Slot `core.settings-sections`): Prüf-Intervall (Tage) und größte Topic-Tiefe.
- **Neu-Dialog:** Memo und Topic hängen als `workspace.create-types` im Menü „＋ Neu“ (`create.memo`, `create.topic` im Namensraum `memos`); die Formulare legen im markierten Projekt an.
- **Dokumente:** der gemeinsame Baustein `DocumentsSection` aus `shared` wie im Backlog (ohne Frage nach der Kurzfassung): Notizen und Specs ansehen, bearbeiten (Version, Konflikt), Notiz-Eintrag anfügen, Spec anlegen.
- Test-IDs: `memos.<element>` aus `memosTestIds`; die des Dokumente-Abschnitts stehen in `sharedTestIds`.

## Plugin `alarms`

`client/src/plugins/alarms/`, benötigt `layout-header-sidebar` und `workspace`. Die Hauptroute `alarms/main` listet die Wecker der gezeigten Projekte als Erinnerungen, gruppiert nach Zeit (`groupAlarms` in `model.ts`: Fällig, Heute, Später, Erledigt) und ohne Label. Jede Karte (`AlarmCard`) zeigt Zeit, Überschrift (`heading`: der Text, sonst der Titel des ersten Elements) und die Elemente als Chips, nicht mehr offene durchgestrichen und ausgegraut; ein Pfeil klappt die Überschrift ganz auf. Bearbeiten, Zurückstellen und Erledigen sind Icons mit Tooltip; ein erledigter Wecker ist ausgegraut, nennt, wann er verschwindet, und bietet nur „Rückgängig“; ein erloschener bietet nichts. Fehler des Servers stehen als Meldung. Ein Klick öffnet den Wecker in der Detailspalte (`AlarmDetail`): oben eine schmale Erinnerungsleiste mit denselben Aktionen (mit Text: Text als Titel; ohne: nur Zeit und Zustand, das Element ist die Überschrift), darunter bei einem Element dieses über `ElementDetail` von `workspace`, bei mehreren Karten zum Wechseln (die erste offen), bei einer freien Erinnerung nichts; ein Element im Papierkorb wird nur genannt. Ein zweiter Klick oder ✕ schließt.

- **API** (`alarmsApi`): `listAlarms({projects, dueOnly})`, `createAlarm` (mit `targets`), `updateAlarm`, `snoozeAlarm`, `finishAlarm`, `reopenAlarm`; die Ereignisse `alarms.*`, `workspace.element.changed` und `core.reconnected` laden neu.
- **Slot `workspace.detail-sections`** (von `workspace` angeboten): `DetailSections({uid, label, projectUid})` rendert die Widgets der Plugins; `useDetailElement()` liefert dem Widget das Element. `backlog/ItemDetail` und `memos/MemoDetail` binden `DetailSections` ein; `alarms` hängt dort „Wecker stellen“ ein (legt einen Wecker an, der an das Element erinnert) und listet die noch wartenden Wecker des Elements.
- **Formular** (`AlarmForm`, auch im Neu-Dialog als `workspace.create-types`): Zeitpunkt, Elemente über die Suche (Mehrfachauswahl) und Text; der Text ist nur ohne Elemente Pflicht.
- **Fällige Wecker** (`AlarmAttention`, Slot `workspace.attention-sources`): melden sich in der Glocke der Projekte, fällig seit ihrer Zeit (bei einem zurückgestellten seit der neuen Zeit), mit den Elementen als Untertitel und Erledigen und Zurückstellen. Die Wahl blendet das Projekt bei Bedarf ein, merkt den Wecker als geöffneten (UI-Zustand `alarms.selected`, den auch `alarms/main` für die Detailspalte nutzt) und öffnet `alarms/main`.
- **Meldung** (`announce.ts`): bei `alarms.due` ein Banner (`banners.show`) und, wenn erlaubt (`canNotify`, Einstellung „Browser-Benachrichtigung“ in `core.settings-sections`), eine `Notification`.
- Test-IDs: `alarmsTestIds`.
