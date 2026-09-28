# STORY-015 — Notes und Specs in der UI schreiben und ändern

## 2026-09-28 — Notizen änderbar

### Discussed

- Notizen sollen nicht nur ergänzbar, sondern auch änderbar sein.

### Decided

- Vorgabe des Projektverantwortlichen: GET holt den Text, PUT setzt den geänderten Text; alternativ hängt POST …/notes einen neuen Eintrag an.
- PUT …/documents/{name} gilt jetzt für Notizen und Specs; version null legt <ID>_notes.md (erste Notizen, Summary nötig) oder eine Spec an; PUT nimmt dafür optional summary an.
- In der UI öffnet „✎ Bearbeiten“ im Dokument-Dialog denselben Editor mit Vorschau für Notizen und Specs; bei Konflikt bleibt der Text, „Aktuellen Stand anzeigen“ und dann „Trotzdem speichern“.
