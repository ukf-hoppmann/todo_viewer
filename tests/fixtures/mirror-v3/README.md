# Beispiele für Format Version 3 (Backlog)

Golden-Files des Backlog-Teils des Markdown-Spiegels: `TODO.md`, `archive.md`
und `items/**` nach Format Version 3 (Abschnitt „Backlog-Einträge“ in
`docs/techdocs/interfaces.md`). Version 3 ist Version 2 ohne das Feld `Area`.

- `valid/`: dasselbe Beispielprojekt wie `tests/fixtures/mirror-v2/valid`, ohne
  `Area` und mit der Kennung „backlog format version 3“.
- `invalid/<code>/`: je Fehlercode eine Kopie von `valid/` mit genau einem
  Fehler. `expected.json` nennt `code`, `file` und `line`.

Alarme und Memos tragen weiter Version 2; ihre Beispiele liegen unter
`tests/fixtures/mirror-v2/`, das auch das Lesen von Version 2 (mit `Area`)
sichert.
