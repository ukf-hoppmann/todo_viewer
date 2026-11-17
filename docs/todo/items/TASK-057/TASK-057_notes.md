# TASK-057 — Mindmap: Zahl, Fortschrittsring, Zustand und Filter am Knoten, Items und Memos im Detail

## State

- Goal/Status: Umgesetzt und im Browser geprüft; wartet auf die Bestätigung des Owners (2026-11-17).
- Next step: Owner bestätigt `Completed`; danach TASK-065 (Markierungen) (2026-11-17)
- Open:
- Decided:
  - Ein Zustandsfilter blendet einen Knoten samt Ast aus; Umhängen sieht weiter alle Knoten (2026-11-17)
  - `get_node_content` meldet je Item `explicit`; nur eigene Zuordnungen lassen sich im Knoten-Detail lösen (Servererweiterung zu TASK-056) (2026-11-17)
  - Der Statusfilter des Backlogs kommt über `useShownStatuses()` aus `backlog`; sind alle oder keine Status durchgelassen, fragt die Mindmap ohne Filter (2026-11-17)
  - Der `StatusFilter` des Backlogs hängt auch in der Seitenleiste der Mindmap, ohne eigenen Zustand (2026-11-17)
  - Seitenansicht als Spalte rechts der Map, per Schalter in der Seitenleiste ausschaltbar; die Wurzel nimmt keine Items an (2026-11-17)
  - Memos werden im Knoten-Detail verlinkt, nicht im Memo-Detail (2026-11-17)
- References: Spec TASK-057_spec.md; Story-Spec STORY-100_spec.md; Doku neubau-client.md, Abschnitt Plugin `mindmap`

State confirmed after entry 2026-11-17 — Plan und Umsetzung (ea1d34805d6a)

## 2026-11-17 — Plan und Umsetzung

### Discussed

- Plan in sieben Abschnitten: Domain-Funktionen (test first), API und Statusquelle, Knotendarstellung mit Filtern, Seitenansicht mit Drag-and-drop, Knoten-Detail, Item-Detail, Integration.
- Zustandsfilter und Äste: Knoten mit seinem Ast ausblenden (empfohlen, damit kein Kind ohne sichtbaren Parent hängt) oder nur den Knoten; freigegeben: mit Ast.
- Lösen im Knoten-Detail: Server meldet `explicit` je Item (empfohlen) oder der Client zeigt immer „Lösen“ und meldet den Fehler an der Zeile; freigegeben: `explicit`. Das erweitert den Vertrag von TASK-056 um ein Feld; kein bestehender Test bricht.
- Alle oder keine Status durchgelassen: der Server liest einen leeren `statuses` als „alle“, „keine“ lässt sich nicht ausdrücken; die Mindmap rechnet dann mit allen.
- Das Vorbild „Entfernt“ im Formular-Editor liegt nicht im Repository; die Seitenansicht ist deshalb eine eigene Spalte neben der Map.

### Decided

- Siehe Kopf.

### Browserprüfung

- Server mit Beispieldaten (Epic, Story, Tasks, vier Knoten, zwei lose Items), Chromium über Playwright. Geprüft: Ring und Zahl am Knoten, Idee gestrichelt, Ziehen eines losen Items auf „Ideen“ (Knoten wechselt von Idee zu Geplant, Item verlässt die Liste), Detail mit geerbten und eigenen Items, Zustandsfilter, Statusfilter „Completed“ ändert die Zahlen (Import 3 → 4, Anzeige 1 → 2), Schalter der Seitenansicht, Knoten im Item-Detail setzen. Keine Konsolenfehler.
- Tests: Client 1288 grün, Server-Tests der Mindmap 118 grün. Der ESLint-Fehler in `usePersistentState.ts` und zwei E501 in `ruff` bestehen schon ohne diese Änderung.
