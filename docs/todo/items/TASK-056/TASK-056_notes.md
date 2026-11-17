# TASK-056 — Mindmap-Server: Items und Memos zuordnen, Vererbung, Summen und Zustand

## State

- Goal/Status: Umgesetzt, geprüft und vom Owner bestätigt (2026-11-17).
- Next step: TASK-057 (Oberfläche) und TASK-065 (Markierungen) in eigenen Sessions (2026-11-17)
- Open:
- Decided:
  - Ein zweiter Knoten für ein Item wird mit `mindmap_item_assigned` abgewiesen; nur mit `replace` ersetzt er den ersten ausdrücklich (2026-11-17)
  - Item eines gelöschten Knotens ohne Parent-Knoten erbt den Knoten seines Item-Parents, sonst „Nicht zugeordnet“ (2026-11-17)
  - Rolle `node` in `workspace_links` (Migration v3 in `workspace`), Richtung Knoten → Item/Memo; die allgemeinen Link-Operationen lehnen sie ab (2026-11-17)
  - `mindmap` benötigt `backlog` (Port `BacklogItems`); `memos` ist nicht nötig, Memos erkennt es am Elementtyp (2026-11-17)
  - Wirksamer Knoten, Summen und Zustand werden bei jeder Abfrage berechnet, nicht gespeichert; Wiederherstellen stellt die Zuordnung so von selbst wieder her (2026-11-17)
  - Zählende Items folgen dem Statusfilter (`statuses`); `Rejected` zählt in der Zahl mit, wenn der Filter es durchlässt, aber nie im Zustand (2026-11-17)
- References: Spec TASK-056_spec.md; Story-Spec STORY-100_spec.md; Doku neubau-server.md, Abschnitt Plugin `mindmap`

State confirmed after entry 2026-11-17 — Bestätigung (cf9ad7f15b8a)

## 2026-11-17 — Plan und Umsetzung

### Discussed

- Plan in fünf Schritten: reine Domain-Funktion (`domain/assignment.py`), Rolle `node` und Migration, Zuordnen/Lösen mit Port und Adapter, Baum-Antwort, Löschregel und Memo-Links.
- Zweiter Knoten: abweisen (Standard) oder ersetzen (`replace`); empfohlen und freigegeben: beides, abweisen als Standard.
- Gelöschter Knoten ohne Parent-Knoten: erben vom Item-Parent (Lesart „als wäre der Knoten nie da gewesen“) oder immer „Nicht zugeordnet“; empfohlen und freigegeben: erben.
- Speicherung: eine Verknüpfung `Knoten → Item/Memo` mit eigener Rolle. Das verlangt die Migration der CHECK-Regel in `workspace_links`.
- Abweichung vom Plan: `memos` steht nicht in `requires`, weil die Mindmap Memos nur über den Elementtyp erkennt; weniger Kopplung.
- Die Zuordnungs-Operationen haben kein Versionstoken (Architektur §3 verlangt es für schreibende Operationen): eine Verknüpfung ändert weder Item noch Knoten, wie bei `add_link`. Vom Owner zu bestätigen.

### Decided

- Siehe Kopf.
- Gezählt wird alles, was der Filter durchlässt, auch `Rejected` (die Story-Spec nennt keine Ausnahme); der Zustand ignoriert `Rejected` und den Filter.

### Open

- Ausnahme vom Versionstoken (siehe oben) bestätigen lassen.

## 2026-11-17 — Bestätigung

### Decided

- Der Owner hat den Task bestätigt (`Completed`). Die Ausnahme vom Versionstoken wurde dabei nicht beanstandet; sie bleibt wie umgesetzt.
