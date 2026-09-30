# STORY-034 — Menüabschnitt „Projekte“: Primärquelle, Pfade und Sync je Projekt

## 2026-09-30 — Umsetzung und Entscheidungen

### Discussed

- Der Bearbeiten-Dialog enthielt Ordner, Sync und Umstellen; das wandert in die Karten des Menüabschnitts Projekte, der Dialog behält nur den Namen.
- Der Status kommt nur auf Anforderung (Beschluss aus STORY-032): beim Laden, bei Fensterfokus, beim Öffnen des Menüs, per Schaltfläche und nach einem Sync, nie im 5-s-Takt.

### Decided

- Karte je Projekt: Primärquelle wechseln (Sync, Backup serverseitig), Markdown-Ordner, Spiegel (Datenbank-Spiegel an/aus, Markdown-Spiegel entfernen), Stand und letzter Sync, Sync mit Richtung (Standard von der Primärquelle zum Spiegel).
- SourceDialog hat einen Modus (full/name/folder) und nutzt den vorhandenen Ordner-Browser weiter; Escape schließt nur den obersten Dialog.
- Das Badge in der Sidebar erscheint bei mirror_changed, both_changed und unreadable (nicht bei primary_changed und unknown); Klick öffnet die Karte dieses Projekts.
- Release v0.6.7.

### Open

- Die Reihenfolge der Projekte bleibt in der Sidebar und ist nicht Teil dieser Story.
- Nicht geprüft: Docker-Image, laufender Container.
