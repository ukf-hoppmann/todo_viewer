# TASK-060 — Mindmap: runde Anordnung, umschaltbar zur Anordnung zur Seite

## State

- Goal/Status: §1 (Prototyp), §2 (`layoutTree(nodes, mode)`) und §3 (UI-State `layout`, Umschalter in der Seitenleiste) erledigt und committet; §4 bis §6 offen (2026-11-18)
- Next step: weiter mit §4 (Seite und Knoten ruft `layoutTree(…, layout)` auf), dann: §4 Seite und Knoten, §5 Drag-and-drop, §6 Integration und Doku.
- Open:
  - Gerade oder gekrümmte Kanten in der runden Anordnung: in der Umsetzung am Bild entscheiden (2026-11-17)
  - Drag-and-drop-Zonen vor/nach links der Wurzel: am Bild prüfen, sonst nur „innerhalb“ (2026-11-17)
- Decided:
  - Die Anordnung gilt für Einzel- und Gesamtansicht und bleibt im UI-State (`layout`) gespeichert (2026-11-17)
  - Der Umschalter sitzt in der Seitenleiste (2026-11-17)
  - Keine neue Abhängigkeit ohne Freigabe des Owners (2026-11-17)
  - Runde Anordnung als eigene Berechnung, Ergebnis des Prototyps in den Notizen von `STORY-101` (2026-11-17)
- References: Spec `TASK-060_spec.md`; Story-Spec `STORY-101_spec.md`

State confirmed after entry 2026-11-18 — §3 umgesetzt: Zustand und Umschalter (77701e247d2e)

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
