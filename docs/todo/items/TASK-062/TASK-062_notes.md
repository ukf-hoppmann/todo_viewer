# TASK-062 — Mindmap: freie Maps je Projekt

## State

- Goal/Status: Geplant; Entscheidungen aus der Besprechung von `STORY-102` übernommen.
- Next step: Plan beim Start der Umsetzung vorstellen.
- Open:
  - Gilt die Seitenansicht „Nicht zugeordnet“ auch in freien Maps? Nicht besprochen; Vorschlag: nur im Projektbaum (2026-11-19)
- Decided:
  - Auswahl der Maps als Liste in der Seitenleiste (Projektbaum zuerst, dann freie Maps); dort auch Anlegen, Umbenennen, Löschen (2026-11-19)
  - Die Gesamtansicht zeigt nur Projektbäume, keine freien Maps (2026-11-19)
  - Freie Map löschen: Papierkorb mit Wiederherstellen; der Projektbaum lässt sich nicht löschen (2026-11-19)
  - Keine eigene Map je Memo; ein Memo wird an einen Knoten oder eine freie Map verlinkt (2026-11-19)
  - Freie Maps gehören zu einem Projekt, Übergreifendes zum Projekt „Allgemein“ (2026-11-19)
- References: Spec `TASK-062_spec.md`; Story-Spec `STORY-102_spec.md`; Konzept `EPIC-008_spec.md`; Mockup https://claude.ai/artifact/3qoj9AET4gmLVxg4Nx8gGw; Memo `MEMO-003`

State confirmed after entry 2026-11-19 — Übernahme der Entscheidungen aus STORY-102 (f484bfc2bfb7)

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
