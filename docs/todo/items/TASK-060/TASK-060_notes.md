# TASK-060 — Mindmap: runde Anordnung, umschaltbar zur Anordnung zur Seite

## State

- Goal/Status: §1 (Prototyp), §2 (`layoutTree(nodes, mode)`) und §3 (UI-State `layout`, Umschalter) und §4 (Seite und Knoten folgen `layout`) und §5 (Browserprüfung, Kanten, Drag-and-drop) erledigt und committet; §6 (Integration, Techdocs) offen (2026-11-18)
- Next step: weiter mit §6 (Gesamtlauf der Tests, Lint, Techdocs, Prüfung der Kriterien, dann `Awaiting confirmation`), dann: §4 Seite und Knoten, §5 Drag-and-drop, §6 Integration und Doku.
- Open:
  - Gerade oder gekrümmte Kanten in der runden Anordnung: in der Umsetzung am Bild entscheiden (2026-11-17)
- Decided:
  - Kanten bleiben gekrümmt (React Flow `default`), mit Anschlüssen auf vier Seiten; in der runden Anordnung nach Lage des Kindes (waagerecht oder senkrecht), zur Seite wie bisher rechts nach links (2026-11-18)
  - Drag-and-drop in der runden Anordnung: rechts der Wurzel wie bisher, links vertauschen „vor“ und „nach“ (die Marke liegt dort, wo der Knoten landet), oberhalb und unterhalb der Wurzel nur „innerhalb“ (2026-11-18)
  - Die Anordnung gilt für Einzel- und Gesamtansicht und bleibt im UI-State (`layout`) gespeichert (2026-11-17)
  - Der Umschalter sitzt in der Seitenleiste (2026-11-17)
  - Keine neue Abhängigkeit ohne Freigabe des Owners (2026-11-17)
  - Runde Anordnung als eigene Berechnung, Ergebnis des Prototyps in den Notizen von `STORY-101` (2026-11-17)
- References: Spec `TASK-060_spec.md`; Story-Spec `STORY-101_spec.md`

State confirmed after entry 2026-11-18 — §5: Browserprüfung, Kanten und Drag-and-drop (8ba9a8112e52)

## 2026-11-17 — Anlage aus der Planung der Story

### Discussed

- Planung der Story `STORY-101` mit dem Owner.
- Das Ergebnis des Prototyps gehört laut Kriterium 1 in die Notizen der Story, nicht in diese.

### Decided

- Umschalter in der Seitenleiste, Wahl im UI-State

### Open

- Welcher Algorithmus rund anordnet, entscheidet der Prototyp

## 2026-11-17 — Prototyp und Plan

### Discussed

- Plan mit sechs Abschnitten vorgelegt (Prototyp, Layout-Funktion, Zustand und Umschalter, Seite und Knoten, Drag-and-drop, Integration); der Owner hat ihn freigegeben und den Start mit dem Prototyp verlangt.
- Der Prototyp (300 Knoten) zeigt: ELK `radial` überlappt (37 bis 50 Paare) und ist rund 13.400 px groß, `mrtree` ordnet nur zur Seite an. Eine eigene Berechnung mit Winkelsektor je Teilbaum und Radius je Knoten bleibt ohne Überlappung bei etwa 3500 × 3700 px. Einzelheiten und Messwerte stehen in den Notizen von `STORY-101`.

### Decided

- Runde Anordnung als eigene Berechnung, keine neue Abhängigkeit

### Open

- Gerade oder gekrümmte Kanten in der runden Anordnung
- Zonen vor/nach beim Ziehen links der Wurzel
- Open from 2026-11-17 (Welcher Algorithmus) resolved: eigene Berechnung

## 2026-11-17 — Stand zum Weitermachen

### Discussed

- Erledigt: Plan §1 (Prototyp); Ergebnis und Messwerte in den Notizen von `STORY-101`; `TASK-060` steht auf `In progress`. Es gibt keinen Code im Repository, nur Notizen und Status; alles ist auf `todo_mindmap` committet und gepusht (Commit `2c05502`). Es gibt keinen eigenen Branch für den Task; die Arbeit läuft direkt auf `todo_mindmap`, das Mergen nach `main` entscheidet der Owner.
- Offen, in dieser Reihenfolge (Plan, im Chat freigegeben, nicht im Backlog gespeichert):
  - §2 `layoutTree(nodes, mode: "side" | "round")` in `client/src/plugins/mindmap/mindmapLayout.ts`, Test zuerst in `tests/implementation/unit/client/plugins/mindmap/mindmapLayout.test.ts` (keine Überlappung bei einer festen großen Map, Wurzel in der Mitte, Geschwister im Uhrzeigersinn, Anordnung zur Seite unverändert).
  - §3 UI-State `layout` (`"side"` Standard) in `state.ts` und eine Sektion der Seitenleiste (`core.sidebar-sections`, `when: ["mindmap/main"]`) mit Test nach dem Muster von `MapFilters.test.tsx`; Test-IDs und Texte `de`/`en`.
  - §4 `MindmapPage.tsx`: Modus an `layoutTree` und in den Layout-Schlüssel; `MindmapNode.tsx`: Anschlüsse links und rechts je als Ziel und Quelle mit fester ID, Kante nach Lage des Kindes zum Elternknoten.
  - §5 Drag-and-drop in beiden Anordnungen prüfen (Playwright), sonst nur „innerhalb“.
  - §6 Integration: Tests, Lint, Typprüfung, Techdocs; danach `Awaiting confirmation`.
- Der Prototyp lag im Scratchpad der Session und ist nicht gesichert. Er ist kein Teil des Repositorys; die Berechnung steht zum Nachbauen hier:
  1. Teilbaum-Blattzahl berechnen (Blatt = 1).
  2. Wurzel in die Mitte; Winkel von -90° im Uhrzeigersinn, je Teilbaum ein Sektor nach Blattzahl, der Knoten liegt auf der Mittellinie seines Sektors.
  3. Knoten nach Tiefe, dann nach Winkel durchgehen; Start-Radius = Radius des Elternknotens + 300 (erste Ebene) bzw. + 260; in 10-px-Schritten nach außen, bis das Rechteck (190 × 36, mit 8 px Abstand) kein bereits gesetztes berührt.
  4. Ergebnis ist die linke obere Ecke (Mitte minus halbe Größe).
- Hinweis für die Seite: Die Pläne `TASK-059` und `TASK-058` ändern dieselbe Seite; `TASK-058` ist gemergt, `TASK-059` noch nicht.

### Decided

- Kein eigener Branch für `TASK-060`; weiter auf `todo_mindmap`

### Open

- Gerade oder gekrümmte Kanten in der runden Anordnung
- Zonen vor/nach beim Ziehen links der Wurzel

## 2026-11-18 — §2 umgesetzt: runde Layout-Funktion

### Discussed

- `layoutTree(nodes, mode: "side" | "round" = "side")` in `client/src/plugins/mindmap/mindmapLayout.ts`; neuer Typ `LayoutMode`. Die Anordnung zur Seite ist unverändert. Die runde Berechnung steht wie im Prototyp (Sektor je Teilbaum nach Blattzahl, Radius je Knoten: Start 300 bzw. +260 hinter dem Elternknoten, Schritt 10 px, Abstand 8 px); dazu ein Raster der gesetzten Rechtecke, damit die Prüfung auf Überlappung bei großen Maps lokal bleibt.
- Tests in `tests/implementation/unit/client/plugins/mindmap/mindmapLayout.test.ts`: feste Map mit 300 Knoten ohne Überlappung, Wurzel in der Mitte, Geschwister im Uhrzeigersinn ab oben, Kinder weiter außen als der Elternknoten, Knoten ringsum, Modus `side` gleich dem Standard. Test zuerst: drei schlugen vorher fehl, danach 10 von 10 grün; alle 156 Mindmap-Tests grün, `tsc -b` sauber.
- `npm run lint` meldet 5 Fehler in `client/src/core/ui-state/usePersistentState.ts` (`react-hooks/refs`); sie bestehen schon ohne diese Änderung (mit `git stash` geprüft) und sind nicht Teil dieses Tasks.

### Decided

- Siehe Stand oben; keine neue Entscheidung

### Open

- Gerade oder gekrümmte Kanten in der runden Anordnung
- Zonen vor/nach beim Ziehen links der Wurzel

## 2026-11-18 — §3 umgesetzt: Zustand und Umschalter

### Discussed

- `useMindmapState` (`state.ts`) hat `layout` (`"side"` | `"round"`, Standard `"side"`, Eigentümer `mindmap`); neue Sektion `LayoutSwitch.tsx` (zwei Umschalter „Zur Seite“ / „Rund“, `ToggleButtonGroup`), im Slot `core.sidebar-sections` (`name: "layout"`, `order: 19`, `when: ["mindmap/main"]`, also vor dem Filter); Test-IDs `layoutSwitch`, `layoutOption(value)`, Texte `layout.*` in `de` und `en`. Drückt man den gedrückten Knopf noch einmal, bleibt die Wahl.
- Test zuerst (`LayoutSwitch.test.tsx`, schlug vorher fehl, weil das Modul fehlte); danach 5 neue Tests und alle 161 Mindmap-Tests grün, `tsc -b` sauber; Lint nur die 5 alten Fehler in `usePersistentState.ts`.
- Der Umschalter hat noch keine Wirkung auf die Karte: die Seite liest `layout` erst in §4.

### Decided

- Der Umschalter liegt vor den Filtern (`order: 19`)

### Open

- Gerade oder gekrümmte Kanten in der runden Anordnung
- Zonen vor/nach beim Ziehen links der Wurzel

## 2026-11-18 — §4 umgesetzt: Seite und Knoten

### Discussed

- `MindmapPage.tsx` liest `layout` aus dem UI-State und ruft `layoutTree(…, layout)` auf; der Modus steckt im Layout-Schlüssel, damit beim Umschalten neu gerechnet und neu eingepasst wird (`fitView`). `MindmapNode.tsx` hat auf beiden Seiten Anschlüsse mit fester ID (`left`, `right`), die Wurzel nur als Quelle, jeder andere Knoten als Ziel und Quelle. Die Kante wählt nach der Lage des Kindes: liegt es links vom Elternknoten, geht sie von dessen linker Seite zur rechten Seite des Kindes, sonst wie bisher von rechts nach links.
- Test zuerst: der Mock von React Flow zeigt jetzt Position, Anschlüsse und Kantenanschlüsse; 5 neue Tests in `MindmapPage.test.tsx` (zur Seite wie bisher, rund mit wanderndem Ast, Anschlüsse, Umschalten hin und zurück) schlugen vorher fehl, danach 166 von 166 Mindmap-Tests grün, `tsc -b` sauber, Lint nur die 5 alten Fehler.
- Nicht geprüft: das Bild im Browser (jsdom hat kein Layout). Der Pfeil zum Falten sitzt weiter am rechten Rand des Knotens, auch bei Ästen links der Wurzel; ob das irritiert, zeigt die Prüfung in §5.

### Decided

- Die Kanten bleiben in der Umsetzung die vorhandenen (React Flow `default`), nur mit den neuen Anschlüssen; ob gerade oder gekrümmt, entscheidet das Bild in §5

### Open

- Gerade oder gekrümmte Kanten in der runden Anordnung
- Zonen vor/nach beim Ziehen links der Wurzel
- Lage des Falt-Pfeils bei Ästen links der Wurzel

## 2026-11-18 — §5: Browserprüfung, Kanten und Drag-and-drop

### Discussed

- Prüfstand: Server aus dem Paket (venv im Scratchpad), Vite, Chromium mit Playwright, Beispielprojekt mit 110 Knoten; Skripte nur im Scratchpad. Ein nativer Drag lässt Chromium in dieser Umgebung abstürzen; deshalb löste das Skript `dragstart`, `dragover`, `drop` und `dragend` selbst aus (dieselben Handler der Seite).
- Bild der runden Anordnung: gut lesbar, keine Konsolenfehler, Umschalten hin und zurück passt die Ansicht neu ein, die Anordnung zur Seite sieht wie vorher aus.
- Kanten: mit Anschlüssen nur links und rechts schwingen Kanten zu Knoten oberhalb oder unterhalb des Elternknotens stark. Entscheidung: vier Anschlüsse je Knoten; `edgeSides(mode, parent, child)` in `mindmapLayout.ts` wählt in der runden Anordnung waagerecht, wenn das Kind mehr daneben als darüber liegt, sonst senkrecht; zur Seite immer rechts nach links. Gekrümmte Kanten bleiben (Optionen gerade oder gekrümmt: gekrümmt liest sich besser, kein Mehraufwand).
- Drag-and-drop: Einfügen davor, danach und innerhalb ergab links und rechts der Wurzel die richtige Reihenfolge am Server. Befund im Bild: links der Wurzel liegen frühere Geschwister weiter unten, die Marke „vor“ oberhalb des Ziels stand also dort, wo der Knoten nicht landet. Optionen: (a) überall nur „innerhalb“ (verliert das Umordnen), (b) „vor“ und „nach“ links vertauschen und oben/unten nur „innerhalb“ anbieten (empfohlen: die Marke zeigt, wo der Knoten landet, geordnet wird weiter dort, wo es eindeutig ist), (c) nach Tangente der Äste mit schrägen Zonen (zu aufwendig). Gewählt: (b), `dropZonesOf` in `mindmapLayout.ts`, `zones` am Knoten, `data-side` an der Marke.
- Tests zuerst (schlugen vorher fehl): Anschlüsse auf vier Seiten, Kanten senkrecht, `edgeSides` (3), `dropZonesOf` (4), Drag in der runden Anordnung (4); danach 179 von 179 Mindmap-Tests grün, `tsc -b` sauber, Lint nur die 5 alten Fehler.
- Nicht geprüft: der Falt-Pfeil bleibt am rechten Knotenrand, auch bei Ästen links der Wurzel; im Bild unauffällig, nicht weiter geändert. Eine Map mit 300 Knoten wurde nur im Prototyp und im Test geprüft, nicht im Browser (dort 110 Knoten).

### Decided

- Kanten gekrümmt, mit Anschlüssen auf vier Seiten
- Zonen: rechts wie bisher, links vertauscht, oben und unten nur „innerhalb“

### Open

- Open from 2026-11-17 (Gerade oder gekrümmte Kanten) resolved: gekrümmt
- Open from 2026-11-17 (Zonen vor/nach links der Wurzel) resolved: vertauscht links, nur „innerhalb“ oben und unten
