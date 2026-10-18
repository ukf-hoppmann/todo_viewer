# STORY-037 — Architekturregeln für Topics, Notes und Links

## 2026-10-08 — Vorbereitung der Umsetzung

### Discussed

- Konflikte der Notes mit architecture.md §1 und backend.md §5
- Wie ein Link ein Item in einem Markdown-Projekt findet, das keine uid hat

### Decided

- Notes, Topics, Links und Auslöser liegen nur in der zentralen Datenbank, unabhängig von der Primärquelle des Projekts (Entscheidung des Besitzers, EPIC-005).

### Open

- Link-Ziel: Projekt plus Item-Label, vom retype-Use-Case mitgeführt, statt uid (Vorschlag, braucht Freigabe)
- Die Regeländerungen werden erst nach Freigabe des Besitzers verbindlich

## 2026-10-08 — Regeln freigegeben und umgesetzt

### Discussed

- Regeländerungen aus der Spec

### Decided

- Besitzer hat die Regeln freigegeben: architecture.md §3, backend.md §5/§6, web.md §5
- Link-Ziel ist Projekt + Item-Label; RetypeService führt die Links in derselben Operation mit
- Import-Linter-Vertrag: Markdown-Adapter kennt keine Notes
