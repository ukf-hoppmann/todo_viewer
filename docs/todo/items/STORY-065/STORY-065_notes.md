# STORY-065 — Generischer Sync-Dienst über Datenbank und Dateien

## 2026-10-16 — Entscheidungen

### Decided

- Markdown bleibt als Spiegel mit Sync, weil in der Cloud nur mit .md gearbeitet werden kann; Cloud-Einträge werden lokal eingesammelt und in die DB übernommen.
- Der Sync muss später abschaltbar sein, ohne dass die Plugins es merken.
- Zuordnung nur über die UUID; das Label ist Anzeige.
- Zwei Infrastrukturen (Datenbank, Dateien); der Sync ist ein Dienst über beiden Ports.
