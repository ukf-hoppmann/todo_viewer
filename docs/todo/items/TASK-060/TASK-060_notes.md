# TASK-060 — Mindmap: runde Anordnung, umschaltbar zur Anordnung zur Seite

## State

- Goal/Status: Spec steht; Prototyp fertig, Algorithmus gewählt (eigene Berechnung); Umsetzung beginnt.
- Next step: Umsetzung nach dem Plan: §2 Layout-Funktion (Test zuerst), §3 Zustand und Umschalter, §4 Seite und Knoten, §5 Drag-and-drop, §6 Integration und Doku.
- Open:
  - Gerade oder gekrümmte Kanten in der runden Anordnung: in der Umsetzung am Bild entscheiden (2026-11-17)
  - Drag-and-drop-Zonen vor/nach links der Wurzel: am Bild prüfen, sonst nur „innerhalb“ (2026-11-17)
- Decided:
  - Die Anordnung gilt für Einzel- und Gesamtansicht und bleibt im UI-State (`layout`) gespeichert (2026-11-17)
  - Der Umschalter sitzt in der Seitenleiste (2026-11-17)
  - Keine neue Abhängigkeit ohne Freigabe des Owners (2026-11-17)
  - Runde Anordnung als eigene Berechnung, Ergebnis des Prototyps in den Notizen von `STORY-101` (2026-11-17)
- References: Spec `TASK-060_spec.md`; Story-Spec `STORY-101_spec.md`

State confirmed after entry 2026-11-17 — Prototyp und Plan (2ef4c59032e5)

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
