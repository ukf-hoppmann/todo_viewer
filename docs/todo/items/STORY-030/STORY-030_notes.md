# STORY-030 — Sync mit wählbarer Richtung, voller Umfang, Wechsel der Primärquelle

## 2026-09-30 — Was schon da war und was fehlte

### Discussed

- Sync in beide Richtungen, voller Umfang, kein Löschen ohne Bestätigung, sync_required beim Wechsel und kein automatischer Sync gab es schon.
- Es fehlten die Standardrichtung (direction war Pflicht) und der Nachweis für Markdown-primär mit Datenbank-Spiegel.

### Decided

- direction ist optional: Standard von der Primärquelle zum Spiegel (Datenbank-Projekt to_md, Markdown-Projekt from_md).
- Der SyncService blieb unverändert; drei neue Integrationstests belegen, dass er für Markdown-primär genauso arbeitet.
- Release v0.6.2.
