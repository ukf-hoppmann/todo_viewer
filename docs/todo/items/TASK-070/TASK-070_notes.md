# TASK-070 — Oberfläche ohne Area

## State

- Goal/Status: Umgesetzt und geprüft; wartet auf Bestätigung des Owners (2026-11-23).
- Next step: Owner bestätigt `Completed`; danach `TASK-071` (Area aus Server und Datenbank entfernen) (2026-11-23).
- Open:
  - Nichts offen (2026-11-23)
- Decided:
  - In der Oberfläche steht das Thema im Abschnitt „Knoten“ der Mindmap (bestand schon); ein eigener Ersatz für Area ist nicht nötig (Zuschnitt) (2026-11-23)
  - Formular, Detail und Beförderungsdialog kennen kein `area` mehr; `listAreas` und alle Übersetzungen entfernt (2026-11-23)
  - `schema.d.ts` neu erzeugt (`scripts/gen-api.sh`): nur zwei Kommentare, Rest von `TASK-069` (2026-11-23)
- References: Spec `TASK-070_spec.md`; Story `STORY-106` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: TASK-069

State confirmed after entry 2026-11-23 — Umsetzung (6ec0755778c6)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-106

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-106 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-106_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- In der Oberfläche steht das Thema im Abschnitt „Knoten“ der Mindmap (bestand schon); ein eigener Ersatz für Area ist nicht nötig (Zuschnitt)

### Open

- Nichts.

## 2026-11-23 — Umsetzung

### Discussed

- Test zuerst: Tests angepasst (kein Feld Area im Formular und Detail, kein `area` in den gesendeten Feldern, kein Aufruf von `backlog/areas`), sie schlugen aus dem erwarteten Grund fehl; danach der Code.
- Geändert: `ItemForm`, `ItemDetail`, `backlog/api.ts`, `PromoteDialog`, Übersetzungen beider Plugins (de, en), Fake-Backend der Tests; README und `neubau-client.md` ohne Bereich.
- `areaOf` und `TreeView.area` bleiben (hinterlegte Fläche im Baum, kein Feld). Der Abschnitt „Knoten“ (Slot `backlog.item-detail`) blieb unverändert; sein Test läuft grün.
- Beim Einrichten der Umgebung lief der Typ-Test des OpenAPI-Schemas erstmals (vorher übersprungen, `node_modules` fehlte) und zeigte veraltete Kommentare in `schema.d.ts` aus `TASK-069`; neu erzeugt.
- `npm run lint` meldet 5 Fehler in `core/ui-state/usePersistentState.ts` (react-hooks/refs). Sie bestehen ohne meine Änderung genauso (mit `git stash` geprüft) und gehören nicht zu dieser Task.

### Decided

- Lint-Fehler in `usePersistentState.ts` nicht in dieser Task behoben (fremde Datei, parallele Session).

### Open

- Die Lint-Fehler in `usePersistentState.ts` sind ein eigenes Thema; der Owner entscheidet, ob dafür ein Item entsteht.
