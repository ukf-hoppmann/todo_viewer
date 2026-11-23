# Beispiele für das Mindmap-Format Version 1

Beispiele für den Mindmap-Spiegel (Format: Abschnitt „Mindmap-Dateien (Format Version 1)“ in
`docs/techdocs/interfaces.md`). Sie sind die Golden-Files des `MindmapCodec`.

- `valid/mindmap/`: ein vollständiges, gültiges Projekt namens `Beispiel`: der Projektbaum, zwei freie Maps (eine im
  Papierkorb), ein Knoten in zwei Bäumen (`NODE-005`, `NODE-007`), Knoten mit Markierung, Zuordnungen von Items und
  Memos (auch eines anderen Projekts), ein Knoten im Papierkorb mit entfernter Platzierung, Dokumente (`NODE-001_*`)
  sowie ein neuer Knoten und eine neue Map aus der Cloud mit Platzhaltern (`new-cloud-ast`, `new-cloud-entwuerfe`).
  Beim Schreiben müssen genau diese Bytes entstehen.
- `invalid/<code>/files/`: je Fehlercode eine Kopie von `valid/` mit genau einem Fehler. `expected.json` nennt `code`,
  `file` und `line` des Fehlers, den das Lesen melden muss, und den Grund.

Der Spiegel liest `mindmap/**/*.md`; `files/` enthält deshalb den Ordner `mindmap/`.
