# STORY-031 — Backup vor dem Wechsel der Primärquelle

## 2026-09-30 — Umsetzung und Entscheidungen

### Discussed

- Nach dem Wechsel schreibt der nächste Sync to_md den Markdown-Ordner neu und normalisiert Handschrift (Kopfzeilen, Umbruch, Feldreihenfolge); deshalb ist das Backup bei Markdown eine Byte-Kopie.
- Die Wahl zwischen Byte-Kopie und Export trifft ein Routing-Adapter (Port RawBackup), nicht der Service; der Datenbank-Adapter meldet, dass er nicht kopiert, dann exportiert BackupService über den SyncService.

### Decided

- Ort: <CONFIG_DIR>/backups/<Projekt>_<id8>/<JJJJMMTT-HHMMSS>/, ein gültiger Backlog-Ordner; kein Schalter, keine automatische Löschung.
- Es gibt keine eigene Restore-Funktion: der Backup-Ordner wird als Markdown-Projekt eingetragen oder per Sync gelesen.
- Fehler: 409 backup_failed mit details.reason; gesichert wird erst nach bestandenem Sync-Check und Validierung.
- Release v0.6.3.

### Open

- Die UI zeigt den Backup-Pfad noch nicht (STORY-034).
- Schreibrechte des Volumes im Container sind nicht geprüft.
