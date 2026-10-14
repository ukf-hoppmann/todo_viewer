# STORY-049 — Notes-Bereich: Filter, Großansicht, Steuerung oben und sichtbare Schachtelung

## 2026-10-09 — Umsetzung

### Discussed

- Filter wirkten nicht, weil Unterthemen mitgezählt werden und der Zähler nur direkte Notes zeigte; Status, fällig und Projekt liefen nicht über die API.

### Decided

- Status, fällig und Projekt filtert der Server (GET /notes/index), die Suche der Browser. Die Großansicht ist ein großer Dialog ohne eigene URL; ein Link auf die Note entfällt vorerst. Die Filter werden nicht dauerhaft gespeichert.

### Open

- Soll die Großansicht eine eigene Adresse (Link) bekommen?
