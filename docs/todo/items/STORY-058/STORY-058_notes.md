# STORY-058 — Konflikte im Sync mit Diff-Ansicht entscheiden

## 2026-10-14 — Anlage (2026-10-14)

### Decided

- Diff-Ansicht im vorhandenen Sync-Dialog; Items feldweise, Texte als Textvergleich; Entscheidungen Datenbank, Datei oder aufschieben.
- Kein Bearbeiten und kein Zusammenführen im Dialog; händisch ändern und erneut abgleichen.

### Open

- Diff-Bibliothek oder eigene Zeilenvergleichsfunktion; neue npm-Abhängigkeit nur nach Rückfrage.

## 2026-10-16 — Umsetzung in der Cloud (Block A bis C) und lokale Abnahme

### Discussed

- Lokale Abnahme am 2026-10-16: scripts/check.sh grün (ruff, mypy strict, import-linter, pytest 1174, tsc, eslint, vitest 334); v0.8.8, Viewer ausgerollt, Schema 9.
- Sichtprüfung am laufenden Viewer (`ezf-ui`, nur Vorschau, nichts ausgeführt): Konfliktliste mit je drei Entscheidungen (vorbelegt: Aufschieben) und „Vergleich anzeigen“; der Vergleich zeigt eine Feldtabelle (z. B. status: In progress | Open) und einen Zeilenvergleich mit − und + für lange Felder.

### Decided

- Eigene Zeilenvergleichsfunktion (längste gemeinsame Teilfolge) statt Bibliothek, keine neue npm-Abhängigkeit.
- Items: Tabelle der unterschiedlichen Felder (Datenbank | Datei), Felder mit Zeilenumbruch oder über 60 Zeichen als Zeilenvergleich; Dokumente als Zeilenvergleich. Beim Umstellen der Primärquelle werden keine Entscheidungen geschickt.

### Open

- Darstellungsfehler: Im Feldvergleich ist die Spalte „Feld“ so schmal, dass Feldnamen wie `status` und `goal` senkrecht umbrechen.
- Sehr große Texte im Vergleich nicht geprüft.
