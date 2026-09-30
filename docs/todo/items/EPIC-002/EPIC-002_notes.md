# EPIC-002 — Notizen

## 2026-09-27 — Anlage

### Discussed

- Beim Zuschnitt von `EPIC-001` blieben die UI-Funktionen für die neuen
  API-Endpunkte offen.

### Decided

- Die UI-Funktionen bekommen ein eigenes Epic statt Stories unter
  `EPIC-001`.
- Die Stories werden erst angelegt, wenn die jeweiligen API-Stories stehen;
  jede UI-Story hängt dann per `Dependencies` an ihrer API-Story
  (`STORY-006` bis `STORY-009`).

### Open

- Zuschnitt der Stories (z. B. Anlegen, Löschen, Felder bearbeiten,
  Notes/Specs) und Bedienkonzept.

## 2026-09-28 — Bedienkonzept

### Discussed

- Inline-Bearbeitung oder eigener Bearbeiten-Modus
- Einstieg zum Anlegen
- Ort des Papierkorbs
- Art des Spec-Editors

### Decided

- Bearbeiten nur über einen eigenen Bearbeiten-Modus mit Speichern/Abbrechen; Inline-Bearbeitung ist zu riskant für versehentliche Änderungen.
- Anlegen über „Neu“ oben (ohne Parent) und „Kind anlegen“ im Detail-Panel.
- Papierkorb als eigene Ansicht neben Baum, Abhängigkeiten und Kanban.
- Spec-Editor als Textfeld mit Markdown-Vorschau, ohne neue Bibliothek.
- Stories STORY-012 bis STORY-015 angelegt.

## 2026-09-30 — Wiedergeöffnet für Typwechsel in der UI

### Discussed

- Der Typ eines Items lässt sich seit v0.1.1 per API ändern (retype); die UI bietet das noch nicht an.

### Decided

- EPIC-002 wird wieder geöffnet; die UI dafür kommt als eigene Story unter EPIC-002.
