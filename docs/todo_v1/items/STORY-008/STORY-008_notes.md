# STORY-008 — Notizen

## 2026-09-28 — Umgang mit zugehörigen Dateien

### Discussed

- Was mit `items/<ID>/` (Notes, Specs) passiert, wenn ein Item gelöscht wird.

### Decided

- Wird ein Item wirklich gelöscht, werden die dazugehörigen Dateien ebenfalls
  gelöscht (Vorgabe des Projektverantwortlichen).
- Archivierte Items dürfen mit denselben Prüfungen gelöscht werden.

### Open

- Rückfrage offen: Sind mit „dazugehörigen items“ nur der Ordner
  `items/<ID>/` gemeint oder auch Kind-Items (kaskadierendes Löschen)?

## 2026-09-28 — Umsetzung

### Decided

- Umgesetzt mit der Lesart „Ordner `items/<ID>/` wird mitgelöscht“; Kinder
  und Abhängigkeiten blockieren das Löschen weiterhin (409
  `item_referenced`). Das ist die sichere Variante, solange die Rückfrage
  offen ist; kaskadierendes Löschen kann ergänzt werden.
- Löschen verlangt die Item-Version, wie das Bearbeiten.
- Die Lifecycle-Regeln gelten auch beim Löschen, z. B. darf das letzte
  Pflichtkind eines laufenden Epics nicht gelöscht werden.

### Open

- Rückfrage an den Projektverantwortlichen: Sollen Kind-Items mitgelöscht
  werden (kaskadierend)?
