# TASK-062 — Mindmap: freie Maps je Projekt

## State

- Goal/Status: Vom Projekteigner am 2026-11-19 bestätigt (`Completed`); auf `main`, Release v0.11.0.
- Next step: Keiner; der Eintrag ist abgeschlossen.
- Open:
  - Keine
- Decided:
  - Auswahl der Maps als Liste in der Seitenleiste (Projektbaum zuerst, dann freie Maps); dort auch Anlegen, Umbenennen, Löschen (2026-11-19)
  - Die Gesamtansicht zeigt nur Projektbäume, keine freien Maps (2026-11-19)
  - Freie Map löschen: Papierkorb mit Wiederherstellen; Knoten nur dieser Map gehen mit (gleicher Löschzeitpunkt); der Projektbaum lässt sich nicht löschen (2026-11-19)
  - Keine eigene Map je Memo; ein Memo wird an einen Knoten verlinkt, auch in freien Maps; die Map selbst ist kein Ziel (2026-11-19)
  - „Nicht zugeordnet“ gibt es nur im Projektbaum (2026-11-19)
  - Freie Maps gehören zu einem Projekt, Übergreifendes zum Projekt „Allgemein“ (2026-11-19)
  - Vorsichtige Annahmen der Umsetzung: Name je Projekt eindeutig (ohne Groß-/Kleinschreibung), höchstens 100 Zeichen; Versionstoken `revision` am Baum; gelöschte Map als eigener Papierkorb-Eintrag (`TrashSource`); Wiederherstellen scheitert bei vergebenem Namen (2026-11-19)
- References: Spec `TASK-062_spec.md`; Story-Spec `STORY-102_spec.md`; Konzept `EPIC-008_spec.md`; Mockup https://claude.ai/artifact/3qoj9AET4gmLVxg4Nx8gGw; Memo `MEMO-003`

State confirmed after entry 2026-11-19 — Umsetzung (c00ce61fe0a7)

## 2026-11-19 — Übernahme der Entscheidungen aus STORY-102

### Discussed

- Auswahl: Drei Wege standen zur Wahl, A Liste in der Seitenleiste (Empfehlung), B Tabs über der Karte, C Dropdown im Kopf. Der Owner wählte A: fester Ort zum Verwalten, Ziele beim Umhängen sichtbar.
- Gesamtansicht: Nur Projektbäume (Empfehlung) oder auch freie Maps als zusätzliche Äste, was bei übertragenen Ästen Doppelungen erzeugt. Der Owner wählte nur Projektbäume.
- Löschen: Papierkorb mit Wiederherstellen (Empfehlung) oder sofort mit Rückfrage. Knoten nur dieser Map gehen mit, übertragene Äste bleiben im anderen Baum, Items fallen wie bei gelöschten Knoten zurück.
- Memo-Map: Eine im Memo gespeicherte Map wurde erwogen und verworfen (zweites Speichermodell, Umhängen schwierig); stattdessen freie Map plus Verknüpfung. Der Export einer Map in ein Memo ist als Idee in `MEMO-003` festgehalten.

### Decided

- Variante A mit Liste in der Seitenleiste; Variante B und C verworfen (Verwalten braucht Zusatzmenü, Maps versteckt).
- Gesamtansicht nur Projektbäume.
- Freie Map in den Papierkorb, Wiederherstellen möglich; Projektbaum nicht löschbar.
- Keine Memo-Map; Cloud-Zugriff auf freie Maps über den Markdown-Spiegel `STORY-105`.

### Open

- Ob die Seitenansicht „Nicht zugeordnet“ auch in freien Maps gilt; nicht besprochen.

## 2026-11-19 — Offene Punkte vor der Umsetzung geklärt

### Discussed

- Memo-Link: Verlinken geht heute nur an Knoten (Rolle `node` in `workspace_links`); ein Baum ist kein Element und die Wurzel einer freien Map kein Knoten. Option 1: nur Knoten (Empfehlung, kein Mehraufwand). Option 2: auch die Map als Element, mit Migration, Verknüpfung und Papierkorb der Map.
- „Nicht zugeordnet“: nur im Projektbaum (Empfehlung) oder auch in freien Maps; Letzteres bräuchte eine Regel, weil „nicht zugeordnet“ sich dann auf Knoten statt auf Bäume bezieht.

### Decided

- Memos hängen nur an Knoten (Owner); die Spec ist korrigiert.
- „Nicht zugeordnet“ nur im Projektbaum (Owner).

### Open

- Keine.

## 2026-11-19 — Umsetzung

### Discussed

- Wie eine Map „in den Papierkorb“ geht, obwohl ein Baum kein Element ist: (a) Baum zum Element machen (Migration, Label, Links – aufwendig und mit dem Owner verworfen für Memo-Links), (b) Weiche Löschung am Baum plus Papierkorb-Eintrag über die vorhandene `TrashSource` von `workspace`. Gewählt (b).
- Die Knoten, die nur in der Map stehen, müssen „mitgehen“: sie werden mit demselben Zeitpunkt wie die Map in den Papierkorb gelegt; Wiederherstellen holt nur Knoten mit genau diesem Zeitpunkt zurück, früher einzeln gelöschte bleiben draußen (wie beim Ast). Ein Knoten einer gelöschten Map ist einzeln nicht wiederherstellbar (`mindmap_tree_in_trash`).
- Knoten in mehreren Bäumen gibt es erst mit `TASK-063`; die Zählung `shared_count` / `kept_elsewhere` für die Rückfrage ist schon da (heute immer 0) und wird von der Oberfläche genutzt.
- Name: eindeutig je Projekt (Verwechslung in der Liste vermeiden), nicht von der Spec verlangt – vorsichtige Annahme; beim Wiederherstellen kann der Name inzwischen vergeben sein, dann Fehler `mindmap_map_name_taken`.
- Migration 1 las die Konstante `TREE_KINDS`; sie ist auf den festen Wert `project` umgestellt, damit spätere Arten nur in eigenen Migrationen stehen.

### Decided

- Umgesetzt wie in der Spec: Operationen `list_maps`, `create_map`, `rename_map`, `delete_map` (HTTP und MCP), `tree` bei `get_tree`, `create_node`, `get_node_content`; Liste „Maps in <Projekt>“ in der Seitenleiste mit Kontextmenü; gewählte Map je Projekt im UI-Zustand.
- Nicht Teil: Umhängen/Übertragen (`TASK-063`), entfernte Platzierungen (`TASK-066`), Papierkorb-Ansicht (`TASK-067`). Der Papierkorb von `workspace` zeigt die Map als Eintrag der Art `mindmap_map`; die Oberfläche dafür ist `TASK-067`.

### Open

- Keine.
