# STORY-024 — Speicher-Backend und Sync in der UI bedienen

## 2026-09-30 — Umsetzung: Backend-Wahl, Sync und Umstellen in der UI

### Discussed

- Die Spec sah das Umschalten per PUT direkt nach einem Sync vor; dafür war zuerst TASK-003 nötig (Sync eines Markdown-Projekts als from_md, PUT mit neuem backend nach dem Sync).

### Decided

- Projekt anlegen: Wahl Markdown-Ordner | Datenbank im SourceDialog; Datenbank braucht einen Namen, der Sync-Ordner ist optional und wird nur gesendet, wenn er getippt oder gewählt wurde.
- Neuer SyncDialog: Richtung, Vorschau (Einträge und Dokumente), Warnliste für Fehlendes mit Checkbox zum Löschen, Ausführen mit dem Token; Ergebnis mit deleted/kept. Im Umstell-Modus ist die Richtung fest, und ohne Löschen-Häkchen bleibt „Übernehmen und umstellen“ gesperrt, solange Fehlendes auf dem Ziel liegt (sonst wären die Seiten nicht gleich und der Server lehnt mit sync_required ab).
- Einstiege: Kürzel „DB“ und ⇄-Knopf in der Sidebar (nur Datenbank-Projekte mit Sync-Ordner), Umstell-Knöpfe im Bearbeiten-Dialog, eigener Text beim Entfernen eines Datenbank-Projekts.
- Die UI schickt language = aktuelle UI-Sprache; Fehlercodes sync_* und project_not_empty sind de/en übersetzt, sync_source_invalid nennt zusätzlich den Grund.
- Reine Logik (Zählen, Löschen-Regel, Richtung beim Umstellen) liegt in src/domain/sync.ts mit eigenen Tests.

### Open

- Nach Datenbank → Markdown bleiben die Datenbank-Daten liegen; ein späteres Zurückstellen zeigt sie in der Vorschau als Unterschied.
- Von Hand geprüft im Dev-Server auf einer Fixture-Kopie mit eigener Scratch-Konfiguration: Projekt anlegen, Umstellen in beide Richtungen, Vorschau mit Warnliste, Ausführen ohne Löschen; nur Deutsch und Englisch kurz angesehen, Fehlerfälle nur in den Tests.
