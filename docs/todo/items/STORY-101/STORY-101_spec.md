# STORY-101 — Spec: Mindmap-Ansichten

Gesamtkonzept: `EPIC-008_spec.md`; der Weg zu den Entscheidungen steht in `STORY-101_notes.md`. Umgesetzt wird es in
`TASK-058` (Fokus, Item-Aktionen), `TASK-060` (runde Anordnung), `TASK-059` (Gesamtansicht) und `TASK-061`
(Abhängigkeiten). Die Tasks laufen nacheinander, jeder in eigener Session auf eigenem `claude/…`-Branch, gemergt nach
`todo_mindmap`. Sie ändern alle `client/src/plugins/mindmap/pages/MindmapPage.tsx`.

## Zweck

Verschiedene Blicke auf dieselbe Map, ohne etwas zu kopieren: einen Ast als Wurzel öffnen, alle Projekte zusammen
sehen, rund oder zur Seite anordnen, Abhängigkeiten zwischen Themen einblenden. Alle Ansichten lesen denselben Baum
(`mindmap/trees/{project}`); keine Ansicht legt Daten an, außer „Erstelle“ am Item.

## Vorhandene Grundlage (Stand `STORY-100`)

- Client: Plugin `client/src/plugins/mindmap/` (`requires`: `layout-header-sidebar`, `workspace`, `backlog`). Seite
  `pages/MindmapPage.tsx` zeigt ein Projekt (`shownProject`: das markierte, sonst das einzige sichtbare), Layout
  `mindmapLayout.ts` (ELK `layered` nach rechts, Knoten 190 × 36), reine Funktionen in `domain/tree.ts`
  (`visibleNodes`, `dropPlacement`, Filter), Zustand in `state.ts` (`usePersistentState`, Eigentümer `mindmap`),
  Sidebar-Sektionen über den Slot `core.sidebar-sections` (`MapFilters.tsx`), Item-Detail über den Slot
  `backlog.item-detail` (`ItemNodeSection.tsx`), Test-IDs in `testIds.ts`.
- Server: Plugin `server/src/viewer/plugins/mindmap/` mit `GetTree`/`TreeOut` (`application/operations.py`), dem
  wirksamen Knoten eines Items (`domain/assignment.py`, `GET mindmap/items/{item}/node` liefert `node_uid` und
  `explicit`) und dem Port `BacklogItems`.
- Routen sind `<owner>/<name>` ohne Pfadparameter (`createAppRouter.tsx`); ein Zustand in der Adresse läuft über
  Query-Parameter.

## Regeln

### Fokus (`TASK-058`)

- Der Fokus ist die Ansicht ab einem Knoten des einen Baums, kein zweiter Baum. Er steht in der Adresse als
  `?focus=<uid>` (Query-Parameter der Route `mindmap/main`), damit die Ansicht per URL erreichbar ist.
- Die Ansicht zeigt einen Pfad von der Projektwurzel bis zum Fokus; jeder Eintrag führt dorthin zurück. Ist der Fokus
  unbekannt oder gelöscht, gilt die Projektwurzel.
- Die Tiefe zählt ab dem Fokus: zwei Ebenen darunter sind ohne eigene Wahl offen. Gefaltet wird wie bisher je Knoten.

### Aktionen am Item (`TASK-058`)

- Drei getrennte Aktionen im Detail eines Items (Slot `backlog.item-detail`):
  - **„Gehe hin“**: öffnet die Map am wirksamen Knoten des Items (`?focus=<Knoten>`). Ist das Projekt des Items
    ausgeblendet, wird es eingeblendet und als gezeigtes Projekt markiert (Owner-Entscheidung 2026-11-17). Hat das
    Item keinen Knoten, öffnet sich die Wurzel des Projekts.
  - **„Erstelle“**: legt unter dem wirksamen Knoten des Items (sonst unter der Wurzel) einen Knoten mit dem Titel des
    Items an und hängt das Item eigens daran (`replace`). Kein Knoten entsteht still im Hintergrund.
  - **„Anker“**: öffnet die Map mit dem eigenen Knoten des Items als Wurzel. Angeboten wird sie nur, wenn das Item
    eigens an einem Knoten hängt (`explicit`).
- Schlägt das Zuordnen nach dem Anlegen fehl, bleibt der Fehler sichtbar; der neue Knoten bleibt stehen (er ist ein
  Thema wie jedes andere und lässt sich im Papierkorb entfernen).

### Anordnung (`TASK-060`)

- Zwei Anordnungen, umschaltbar: **Baum zur Seite** (heute) und **rund** (Wurzel in der Mitte, Äste ringsum). Die Wahl
  gilt für Einzel- und Gesamtansicht und bleibt im UI-State gespeichert (`layout`).
- Welcher Algorithmus rund anordnet (ELK `radial`, `mrtree` oder eine eigene Berechnung), entscheidet ein Prototyp mit
  einer großen Map (etwa 300 Knoten, Knotengröße 190 × 36); Ergebnis und Wahl stehen in den Notizen der Story. In der
  runden Anordnung dürfen sich Knoten nicht überlappen.

### Gesamtansicht (`TASK-059`)

- Einzelansicht = eine Map (ein Projekt); Gesamtansicht = eine gemeinsame Wurzel, darunter die in der Seitenleiste
  gewählten (sichtbaren) Projekte als erste Knoten, jedes mit seinem Baum. Verworfen: mehrere Maps nebeneinander.
- Die Wahl der Ansicht liegt im UI-State (`view`). Projekte hinzu- und wegschalten wirkt sofort.
- Die Summen an der gemeinsamen Wurzel addieren die Projekte; jedes Item zählt einmal (es gehört zu genau einem
  Projekt). Die gemeinsame Wurzel gehört keinem Projekt: an ihr gibt es kein Anlegen, kein Umhängen und kein Zuordnen.
- Fokus gilt auch hier (jeder Knoten, auch ein Projekt, lässt sich als Wurzel öffnen).

### Abhängigkeiten (`TASK-061`)

- Gezeigt werden Abhängigkeiten nur zwischen Themen: eine Linie von Thema A nach Thema B, sobald ein Item aus A
  (samt Unterknoten) ein Item aus B braucht; mehrere Abhängigkeiten ergeben eine Linie mit Anzahl.
- Nur innerhalb eines Projekts (Owner-Entscheidung 2026-11-17): Abhängigkeiten zwischen Items verschiedener Projekte
  erscheinen auch in der Gesamtansicht nicht.
- Die Zusammenfassung liegt in der Server-Domain (Owner-Entscheidung 2026-11-17), weil dort der wirksame Knoten
  berechnet wird. `TreeOut` bekommt `links`; Items im Papierkorb und Items ohne Knoten bleiben außen vor, Linien
  innerhalb eines Knotens (samt Unterknoten) entfallen. Zeigt die Ansicht einen Ast gefaltet oder gefokussiert, enden
  die Linien am sichtbaren Vorfahren (reine Funktion im Client).
- Ein Schalter blendet die Linien ein; Standard aus, der Zustand bleibt gespeichert (`showDependencies`).

### Schalter

- Alle Schalter (Ansicht, Anordnung, Abhängigkeiten) sitzen als Sektionen der Seitenleiste (`core.sidebar-sections`,
  `when: ["mindmap/main"]`), wie `MapFilters`. Die Seite bleibt wie im Backlog aufgebaut (Variante A des Epics).

## Nicht Teil

Freie Maps und das Umhängen von Ästen zwischen Bäumen (`STORY-102`), Überführen ins Backlog (`STORY-103`), KI
(`STORY-104`), Markdown-Spiegel (`STORY-105`), Ersatz des Felds Area (`STORY-106`).

## Abnahme

Die Kriterien der Story; die Kriterien der Tasks sind im jeweiligen Ticket und in `TASK-0xx_spec.md` ausgeführt.
UI-Tests liegen unter `tests/implementation/unit/client/plugins/mindmap/`, Server-Tests unter
`tests/implementation/unit/server/plugins/mindmap/` und `tests/implementation/integration/server/plugins/mindmap/`.
