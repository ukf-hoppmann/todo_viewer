# TASK-053 — Mindmap-Seite: Projektbaum anzeigen, Knoten anlegen, umbenennen, löschen, ein- und ausklappen

## State

- Goal/Status: Umsetzung vorgeplant; wartet auf `TASK-052` und auf vier Antworten des Owners.
- Next step: Die offenen Punkte klären, `TASK-052` umsetzen, dann den Umsetzungsplan zur Freigabe vorlegen.
- Open:
  - Welches Projekt die Seite zeigt; Vorschlag: das markierte, sonst das einzige sichtbare, sonst ein Hinweis (2026-11-16)
  - Was „zwei Ebenen offen“ heißt; Vorschlag: Wurzel, Ebene 1 und Ebene 2 sind zu sehen, ab Ebene 2 ist zugeklappt (2026-11-16)
  - Bedienung in der Map; Vorschlag: Symbole am Knoten beim Überfahren (Unterknoten anlegen, Papierkorb), Umbenennen per Doppelklick direkt im Knoten, keine Detailspalte vor `TASK-055` (2026-11-16)
  - Der ELK-Lader aus `backlog/graphLayout.ts` wird von zwei Plugins gebraucht; Vorschlag: nach `shared` verschieben (2026-11-16)
- Decided:
- References: Konzept `EPIC-008_spec.md`; Notizen `STORY-099`; Server `TASK-052`

State confirmed after entry 2026-11-16 — Vorplanung der Umsetzung (8f3b6c923db2)

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
