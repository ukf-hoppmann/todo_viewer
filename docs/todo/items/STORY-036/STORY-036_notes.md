# STORY-036 — Spiegel-Ordner bleibt beim Ausschalten erhalten

## 2026-09-30 — Umsetzung und Entscheidungen

### Discussed

- Bei einem Datenbank-Projekt war der Markdown-Spiegel nur "sync_path ist gesetzt"; Ausschalten löschte deshalb den Ordner.

### Decided

- Neues Flag mirror_disabled (Migration v5, Standard aus): der Ordner bleibt gespeichert, der Spiegel ist nur abgeschaltet; bestehende Projekte mit Ordner bleiben eingeschaltet.
- mirror none behält den mitgeschickten sync_path, mirror markdown schaltet ohne neuen Pfad wieder ein; der Ordner verschwindet nur, wenn sync_path leer geschickt wird.
- Status und Sync-Schaltflächen behandeln ein ausgeschaltetes Projekt wie eines ohne Spiegel; ein ausdrücklicher Sync über die API und der Wechsel der Primärquelle nutzen den gespeicherten Ordner weiter.
- Menü: Spiegel ausschalten / Spiegel einschalten, der Ordner bleibt sichtbar. Release v0.6.8.

### Open

- Der laufende Container hat noch den Stand vor v0.6.1 bis v0.6.8; bei ./todo.sh update laufen die Migrationen bis v5 (vorher configs/todo.db* sichern).
- Der Backlog-Helper des Harness erkennt dieses Projekt nach der Umstellung auf die Datenbank nicht (legt ein Doppel-Projekt an); Aufgabe als Chip vorgemerkt.
