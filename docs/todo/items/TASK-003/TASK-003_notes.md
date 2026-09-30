# TASK-003 — Backend-Wechsel per PUT nach Sync

## 2026-09-30 — Umsetzung: Backend-Wechsel ohne neue Projekt-Id

### Discussed

- STORY-024 sah das Umschalten per PUT vor, der Server lehnte es aber ab und der Sync lehnte Markdown-Projekte ab. Ein Anlegen eines neuen Projekts hätte die source_id geändert; der Epic-Spec beschreibt dagegen den Ordner-Tausch path/sync_path.

### Decided

- PUT /sources/{id} mit anderem backend stellt das Projekt um, nur wenn beide Seiten gleich sind (SyncService.in_sync); sonst 409 sync_required und nichts ändert sich. backend_change_not_supported entfällt.
- Ein Markdown-Projekt akzeptiert den Sync nur als from_md (Ordner in die Datenbank unter derselben source_id); to_md bleibt sync_same_backend.
- Beim Umstellen wandert der Ordner von path nach sync_path bzw. zurück; path/sync_path im Aufruf werden ignoriert, ein neuer Projektname gilt. Der Markdown-path bleibt eindeutig (409 duplicate).
- Die Markdown-Dateien bleiben nach dem Umstellen liegen; die Datenbank-Kopie bleibt bei Datenbank → Markdown ebenfalls (Daten wandern nur durch Sync, nichts wird automatisch gelöscht). Wird ein Markdown-Projekt ausgetragen, löscht das die Kopie in der Datenbank mit (die Dateien sind die Wahrheit).

### Open

- Ein leeres Datenbank-Projekt lässt sich nicht auf einen Ordner umstellen, den es nicht gibt (400 not_found); der Ordner muss vorher existieren.
