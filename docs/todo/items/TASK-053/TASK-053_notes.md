# TASK-053 — Mindmap-Seite: Projektbaum anzeigen, Knoten anlegen, umbenennen, löschen, ein- und ausklappen

## State

- Goal/Status: Abgeschlossen: vom Owner bestätigt (2026-11-16), nach `todo_mindmap` gemergt.
- Next step: `TASK-054` (Ziehen) startet in einer neuen Session.
- Open:
  - Der Lint meldet 5 Fehler in `core/ui-state/usePersistentState.ts` (bestanden vorher); `npm run build` bricht daran ab, `vite build` allein läuft (2026-11-16)
  - Die Map passt ihren Ausschnitt nach jedem Anlegen, Klappen und Löschen neu ein; ob das beim Arbeiten stört, zeigt der Gebrauch (2026-11-16)
- Decided:
  - Ein Klick öffnet das Detail erst nach 250 ms, damit ein Doppelklick (Umbenennen) die Spalte nicht öffnet (2026-11-16)
  - Die schließbare Detailspalte kommt schon in diesem Task: ein Klick auf einen Knoten zeigt Titel und Text zum Bearbeiten; `TASK-055` ergänzt die Dokumente (2026-11-16)
  - Die Seite zeigt das markierte Projekt, sonst das einzige sichtbare, sonst einen Hinweis „Projekt wählen“ (2026-11-16)
  - „Zwei Ebenen offen“: Wurzel, Ebene 1 und Ebene 2 sind zu sehen, ab Ebene 2 ist zugeklappt; gespeichert werden nur Abweichungen je Knoten (2026-11-16)
  - Bedienung: Symbole am Knoten beim Überfahren (Unterknoten anlegen, Papierkorb), Umbenennen per Doppelklick im Knoten (2026-11-16)
  - Der ELK-Lader zieht aus `backlog/graphLayout.ts` nach `shared` (2026-11-16)
  - Die API-Typen (`schema.d.ts`) werden in diesem Task neu erzeugt; in `todo_mindmap` fehlen die Mindmap-Operationen darin noch (2026-11-16)
- References: Konzept `EPIC-008_spec.md`; Notizen `STORY-099`; Server `TASK-052`, Schnittstelle in `docs/techdocs/neubau-server.md` (Abschnitt „Plugin `mindmap`“)

State confirmed after entry 2026-11-16 — Bestätigung und Merge (a6877d2413ff)

## 2026-11-16 — Vorplanung der Umsetzung

### Discussed

- `TASK-052` ist offen, das Server-Plugin `mindmap` gibt es noch nicht. Die API-Typen des Clients entstehen aus dem OpenAPI-Schema des Servers und dürfen nicht von Hand geschrieben werden; die Seite lässt sich deshalb erst nach `TASK-052` bauen.
- Der Aufbau der Mindmap-Seite ist im Epic `EPIC-008` noch offen; für diesen Task reichen die vier Punkte unter Open.
- Klappzustand: Vorschlag, nur Abweichungen vom Standard je Knoten im UI-Zustand des Servers zu speichern (Besitzer `mindmap`); der Standard ergibt sich aus der Tiefe. So gilt „zwei Ebenen offen“ auch für später angelegte Knoten.
- Anordnung zur Seite: ELK `layered` nach rechts mit beibehaltener Reihenfolge der Geschwister; die runde Anordnung gehört nicht zu diesem Task.
- Löschen läuft über `useDeleteElement` von `workspace` (Rückfrage bei Unterknoten).

### Open

- Welches Projekt die Seite zeigt
- Was „zwei Ebenen offen“ heißt
- Bedienung in der Map
- ELK-Lader nach `shared` verschieben

## 2026-11-16 — Entscheidungen des Owners, Prüfung von TASK-052

### Discussed

- Prüfung von `TASK-052` in `todo_mindmap`: im Archiv `Completed`, Plugin `mindmap` auf dem Server vorhanden, 42 Tests des Plugins grün. Der Typen-Vergleich (`test_openapi_types.py`) wurde ohne `client/node_modules` übersprungen; `client/src/shared/api/schema.d.ts` enthält die Mindmap-Operationen noch nicht.
- Papierkorb läuft über `workspace` (`workspace_delete_element` mit `cascade`); das passt zu `useDeleteElement`.
- `STORY-099` hat inzwischen den Seitenaufbau wie im Backlog entschieden (Sidebar, Baum, schließbare Detailspalte). Der Vorschlag „keine Detailspalte vor `TASK-055`“ passt dazu nur halb: Ohne Detail lässt sich der Text eines Knotens nicht bearbeiten.
- `todo_mindmap` wurde in den Branch der Session gemergt; er enthält zusätzlich vier Commits (Baum zeichnet nur geänderte Zeilen, Tagesbericht), die weder in `main` noch in `todo_mindmap` liegen.

### Decided

- Der Owner nimmt alle vier Vorschläge an: Projektwahl, zwei Ebenen, Bedienung, ELK-Lader nach `shared`
- Die API-Typen werden in diesem Task neu erzeugt

### Open

- Detailspalte mit Titel und Text schon in diesem Task oder erst mit `TASK-055`

## 2026-11-16 — Detailspalte

### Discussed

- Optionen: Detailspalte mit Titel und Text schon jetzt, oder erst mit `TASK-055`. Für jetzt spricht, dass der Text eines Knotens sonst nirgends zu bearbeiten ist und der Seitenaufbau aus `STORY-099` die Spalte vorsieht.

### Decided

- Der Owner entscheidet: Detailspalte schon in `TASK-053`

## 2026-11-16 — Umsetzung

### Discussed

- Plan vom Owner freigegeben und in zehn Abschnitten umgesetzt; Beschreibung in `docs/techdocs/neubau-client.md` (Abschnitt „Plugin `mindmap`“).
- ELK `layered` mit `considerModelOrder` und `forceNodeModelOrder` hält die Reihenfolge der Geschwister; der Test dazu ist grün, eine Alternative war nicht nötig.
- Prüfung im Browser (Chromium, echter Server auf einer Wegwerf-Datenbank): anlegen in drei Ebenen, umbenennen, zuklappen, neu laden (Klappzustand bleibt), Detail mit Text, Blatt und Ast in den Papierkorb; keine Konsolenfehler.
- Dabei gefunden und behoben: neue Knoten lagen außerhalb des Ausschnitts (Map passt jetzt neu ein); der Doppelklick öffnete zwischendurch die Detailspalte und verschob die Map (Klick wirkt jetzt verzögert).
- Kriterien: 1. Hauptroute zeigt den Baum des gewählten Projekts: erfüllt. 2. Anlegen, Umbenennen, Papierkorb, Klappzustand, zwei Ebenen: erfüllt. 3. UI-Tests grün (32 neue, 1227 gesamt), Ablauf im Browser geprüft: erfüllt.

### Decided

- Klick wirkt nach 250 ms (Entscheidung der Umsetzung, siehe Kopf)

### Open

- Lint-Fehler in `usePersistentState.ts` und abbrechendes `npm run build`
- Neu-Einpassen der Map im Gebrauch beobachten

## 2026-11-16 — Bestätigung und Merge

### Decided

- Der Owner bestätigt `TASK-053` als `Completed`; der Branch `claude/compassionate-pascal-a4c5ds` wird nach `todo_mindmap` gemergt

