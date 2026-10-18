# STORY-074 — Abhängigkeiten-Graph

## 2026-10-17 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Zuschnitt.** Die Ansicht ist eine zweite Hauptroute des Plugins `backlog`: `backlog/graph` („Abhängigkeiten“) neben `backlog/main` (Baum); die Filter Status und Priorität in der Seitenleiste gelten für beide (`when` nennt beide Routen), ebenso Projekte und Suche aus `workspace`. Das gewählte Item ist dasselbe wie im Baum (UI-Zustand `backlog`/`selected`); rechts steht dasselbe Detailpanel.
- **Daten.** Der Index von `list_items` nennt je Item die `uid`s seiner Abhängigkeiten (`dependencies`); das ist die einzige Änderung am Server. Die Graph-Domäne (reine Funktionen, Vorlage `src_old/web/src/domain/model.ts` und `views/graphLayout.ts`) baut daraus Knoten und Kanten (nur sichtbare Items mit mindestens einer sichtbaren Abhängigkeit; Kanten zeigen von der Abhängigkeit zum Abhängigen), erkennt zusammenhängende Teilgraphen, rechnet die Nachbarschaft und schaltet Markierungen um.
- **Layout.** ELK „layered“ von links nach rechts; Knoten ohne Abhängigkeiten stehen in der linken Spalte (`LONGEST_PATH_SOURCE`), unabhängige Teilgraphen untereinander. `elkjs` wird erst beim ersten Layout importiert, `@xyflow/react` mit der Seite (Lazy-Import der Seite über die Hauptroute): beide kommen erst beim Öffnen der Ansicht. Beide Pakete sind im Scope client §8 freigegeben.
- **Bedienung.** Auswahl, Hover und ⌘/Strg/⇧-Klick heben Knoten, Kanten und direkte Nachbarn hervor, der Rest wird abgedunkelt; ein Klick auf den gewählten Knoten oder auf den Hintergrund und Esc setzen zurück. Ein Knoten zeigt Priorität (Punkt), Label, Fortschrittsring und den Titel (gekürzt), der Rand trägt die Statusfarbe.
- **Tests.** Domäne zuerst (reine Funktionen, Layout mit echtem ELK im Test); die Seite mit ersetztem `@xyflow/react` (jsdom hat kein Layout), das Hervorheben, die Mehrfachauswahl und Esc an den Eigenschaften der Knoten und Kanten.

### Decided

1. **Server**: `dependencies` im Index; Tests anpassen.
2. **Client Domäne**: `graphModel.ts` (Graph, Teilgraphen, Nachbarschaft, Umschalten) und `graphLayout.ts` (ELK); Tests zuerst.
3. **Seite**: `GraphPage` mit React Flow, Knoten, Hervorheben, Esc; zweite Hauptroute und Filter für beide Routen.
4. **Integration**: `check-next.sh`, `check.sh`, Techdoku.

### Open

- Keine neuen Fragen.

## 2026-10-17 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant: Server `dependencies` im Index; Client `graphModel.ts`, `graphLayout.ts`, `GraphNode.tsx`, `pages/GraphPage.tsx`, zweite Hauptroute `backlog/graph` und die Filter für beide Routen. Beschreibung in `docs/techdocs/neubau-server.md` und `neubau-client.md`. Die Pakete `@xyflow/react` und `elkjs` sind in `client/package.json` ergänzt (im Scope client §8 freigegeben).
- Die Seite ist eine Hauptroute neben dem Baum (nicht eine Unterseite im Sinn eines Sidebar-Eintrags), weil der Plugin-Vertrag Unterseiten nur für Hauptrouten mit Seitenleiste kennt (`STORY-071`, Frage 27).

### Decided

- Abschlusskriterien geprüft: (1) die Ansicht zeigt nur Items mit Abhängigkeiten, Layout ELK von links nach rechts (`graphLayout.test.ts` mit echtem ELK, `GraphPage.test.tsx`); (2) Auswahl, Hover und ⌘/Strg/⇧-Klick heben Knoten, Kanten und Nachbarn hervor, Esc setzt zurück (`graphModel.test.ts`, `GraphPage.test.tsx`; dort ist `@xyflow/react` ersetzt, weil jsdom kein Layout hat); (3) die Bibliotheken werden erst beim Öffnen geladen: `vite build` legt `GraphPage` und `elk.bundled` in eigene Teile (Ausgabe geprüft); (4) die Tests der Graph-Domäne sind grün.
- `scripts/check-next.sh` und `scripts/check.sh` grün. Status: `Awaiting confirmation`.

### Open

- Nicht geprüft: das Zeichnen im echten Browser (React Flow braucht Layout); die Größe der Teile ist nicht begrenzt (ELK ist rund 1,4 MB, geladen nur beim ersten Öffnen).
