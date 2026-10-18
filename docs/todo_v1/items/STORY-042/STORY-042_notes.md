# STORY-042 — Beförderung und Rückstufung zwischen Note und Item

## 2026-10-08 — Vorbereitung der Umsetzung

### Discussed

- Pflichtfelder bei Beförderung
- Bedingungen der Rückstufung
- Notizen und Specs in beide Richtungen

### Decided

- Beförderung: Pflichtfelder liefert der Aufrufer, die UI zeigt ein vorausgefülltes Formular, alle Backlog-Prüfungen laufen.
- Rückstufung nur bei Status Open, ohne Kinder, nicht Parent oder Dependency eines anderen Items.
- Notizen und Specs wandern in beide Richtungen mit.

### Open

- Zwei Speicher (Markdown-Projekt und Datenbank) haben keine gemeinsame Transaktion; die Reihenfolge und Wiederholbarkeit werden in der Umsetzung festgelegt.
- Wie wird der Langtext in die datierten Notizen-Einträge eines Items abgebildet (Vorschlag: erster Eintrag)?

## 2026-10-08 — Aufteilung in Tasks

### Discussed

- Story in TASK-013 (Note zu Item), TASK-014 (Item zu Note), TASK-015 (UI-Dialoge) geteilt.

### Decided

- Rückstufung schließt das Item mit Status Rejected und Resolution 'zur Notiz zurückgestuft' (Vorschlag, in TASK-014 so festgelegt).

### Open

- Besitzer bestätigt: Rejected statt Completed für zurückgestufte Items?

## 2026-10-08 — Oberfläche

### Discussed

- TASK-015 (Dialoge) wurde mit STORY-045 umgesetzt, weil das Fällig-Modal (TASK-022) den PromoteNoteDialog braucht.

### Decided

- Beide Richtungen sind über API und UI bedienbar; Herkunft ist an Note und Item verlinkt; Ablehnungen erscheinen als lokalisierte Texte.
