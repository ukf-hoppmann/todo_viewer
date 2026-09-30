# STORY-018 — Typ eines Items in der UI ändern

## 2026-09-30 — Zuschnitt der UI

### Discussed

- Der Hinweis der API auf Verweise außerhalb des Backlogs (notices, Code external_references_may_remain) soll in der UI sichtbar sein. Das Detail-Panel wird nach dem Wechsel neu aufgebaut (Schlüssel = uid), ein Hinweis im Dialog ginge verloren.

### Decided

- Typwechsel per Dialog im Detail-Panel; Zieltypen ohne den aktuellen, Epic nur ohne Parent. Nach dem Wechsel wird das Item unter der neuen ID ausgewählt, der Hinweis liegt im Zustand von App.tsx und bleibt, bis er geschlossen wird. Die UI übersetzt den Code, message dient als Rückfall.
