# STORY-021 — SQLite-Adapter für Items, Archiv, Papierkorb und Dokumente

## 2026-09-30 — Entscheidungen vor dem Plan

### Discussed

- Dokumente: Der DocumentStore-Port ist heute pfadbasiert (domain/documents.py berechnet items/<ID>/…, RetypePlanner liefert Dateiumbenennungen).
- Verweise auf nicht vorhandene Items in der DB.
- Wie ein Datenbank-Projekt vor STORY-022 über die API entsteht.
- Konfiguration der DB-Verbindung.

### Decided

- Der Dokument-Port wird vorher itembasiert umgebaut (STORY-027, Vorgänger dieser Story).
- Die DB lehnt Verweise auf nicht vorhandene Items ab (Fremdschlüssel); der Import meldet sie später in der Sync-Vorschau als Fehler.
- Bis STORY-022 darf eine Quelle in config.json "backend": "database" tragen; path ist dann ein frei gewählter Projektschlüssel.
- Keine Umgebungsvariablen: storage_url steht in config.json, Standard sqlite:///<config_dir>/todo.db.
