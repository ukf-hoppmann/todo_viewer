# TASK-014 — Offenes Item zur Note zurückstufen (Backend)

## 2026-10-08 — Umsetzung Rückstufung (Backend)

### Discussed

- Status des zurückgestuften Items: Rejected oder Completed.

### Decided

- Besitzer hat Rejected bestätigt: das Item wird mit Resolution 'zur Notiz zurückgestuft' abgeschlossen (Markdown-Backend schreibt sie mit Schlusspunkt). Open nach Rejected ging ohne Zwischenstatus.
- Neue Route POST /api/v2/items/{source_id}/{item_id}/demote, Body {version, topic?}, Antwort {item, note}.
- Neue Fehlercodes (409): demote_not_open, demote_has_children (auch geschlossene Kinder, Details items), demote_referenced (Parent oder Dependency eines Items, das nicht im Papierkorb liegt), demote_document_name (Item-Dokument, das unter einer Note-Label nicht benannt werden kann; Prüfung vor jeder Änderung).
- Ablauf: Prüfen, Note anlegen (Kurzfassung = Titel, Langtext = Zusammenfassung), sofort Link origin, Item-Dokumente als <NOTE>_notes.md/<NOTE>_spec*.md, dann Item auf Rejected. Wiederholung mit gleicher Item-Version nutzt die offene Note mit origin-Link weiter (eine beförderte, archivierte Note zählt nicht).
- Der Abschluss löst keinen Hinweis aus (Link-Rolle origin, nicht reference).
- Restfenster wie bei TASK-013: scheitert der Link origin direkt nach dem Anlegen der Note, entsteht bei Wiederholung eine zweite Note.
