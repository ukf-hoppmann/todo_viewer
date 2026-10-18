# STORY-032 — Sync-Status: Spiegel extern geändert erkennen

## 2026-09-30 — Umsetzung und Entscheidungen

### Discussed

- Der Sync kannte keinen Stand "zuletzt synchronisiert"; SyncPreview vergleicht nur die Seiten jetzt und sagt nicht, welche sich bewegt hat.
- Die UI fragt alle 5 s; der Status liest pro Projekt mit Spiegel beide Seiten.

### Decided

- Nach jedem Sync über die API werden ein Fingerabdruck beider Seiten und die Zeit gespeichert (Migration v4); der Status vergleicht die heutigen Fingerabdrücke damit.
- Zustände: none, in_sync, mirror_changed, primary_changed, both_changed sowie unknown (nie synchronisiert, Seiten verschieden) und unreadable (Seite nicht lesbar); gleiche Seiten zählen immer als in_sync.
- Lesen schreibt nie und synchronisiert nie; das Backup zeichnet nichts auf; Änderung von Ordner, Spiegel oder Primärquelle setzt den Stand zurück.
- Kein Cache: gemessen 13 ms pro Projekt mit Spiegel bei 42 Items (Kopie von docs/todo), gegenüber 0,9 ms für den Überblick; Release v0.6.4.

### Open

- Bei sehr großen Backlogs wächst die Zeit linear; dann braucht es einen Cache.
- Das Badge zeigt erst STORY-034.

## 2026-09-30 — Umbau: Status nur auf Anforderung

### Discussed

- Der Status hing an GET /backlog und GET /sources und wurde damit alle 5 s der UI-Abfrage berechnet, obwohl er sich nur bei einer Änderung oder einem Sync ändert; 13 ms je Projekt mit Spiegel.

### Decided

- sync verschwindet aus den Projektantworten; neu GET /sources/{id}/sync-status und GET /sync-status, die auf Anforderung rechnen (UI: beim Öffnen des Menüs, per Schaltfläche, bei Fensterfokus, nach einem Sync).
- Berechnung, Speicherung und Zustände bleiben.
- Der Projekteigner legt fest: Version v0.6.5 (Patch; die Funktion ist in Entwicklung und noch nicht im Einsatz).
