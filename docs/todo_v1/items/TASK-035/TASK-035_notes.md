# TASK-035 — Markdown-Format Version 2 festlegen

## 2026-10-16 — Entscheidungen

### Decided

- Das Format wird in diesem Projekt definiert; der Harness wird danach vom Projektinhaber angepasst.
- Jeder Eintrag trägt seine UUID auch in der .md; das Label ist nur Anzeige.
- Neue Einträge aus der Cloud bekommen ihr Label beim Import, wie heute bei Notes.
- Alles wird gespiegelt, soweit möglich: Backlog, Notes, Topics, Verknüpfungen, Wecker.

## 2026-10-16 — Verweise und Platzhalter

### Discussed

- Vorschlag des Projektinhabers: bei Weckern das Ziel per UUID statt Label angeben, weil sich Labels ändern können.
- Gegenargumente: eine LLM müsste UUIDs abschreiben (Tippfehler fallen nicht auf); zwei Felder (UUID und Label) können sich widersprechen; dasselbe Problem hätten Parent, Dependencies, Topic und Links.

### Decided

- Verweise stehen in den Dateien immer als Label; die Uid steht nur am Eintrag selbst.
- Die DB verweist über uid; der Codec schreibt immer das aktuelle Label des Ziels.
- Die DB merkt sich jedes Label, das ein Element je hatte (Label-Historie in STORY-068); ein Verweis auf ein früheres Label findet weiter dasselbe Element.
- Neue Notes und Topics behalten die heutige Schreibweise (notes/new-<kurzname>.md, '- NEW | <Name>'); nur Backlog-Einträge und Wecker bekommen den Platzhalter NEW-<kurzname>. Weicht von der ursprünglichen Spec ab, damit der Harness weniger ändern muss.

### Open

- Freigabe des gesamten Formats durch den Projektinhaber.

## 2026-10-16 — Format freigegeben und geschrieben

### Decided

- Der Projektinhaber hat Format Version 2 am 2026-10-16 freigegeben.
- Abschnitt 'Dateiformat Version 2' in docs/techdocs/interfaces.md geschrieben.
- Beispiele unter tests/fixtures/mirror-v2/: valid/ (Projekt 'Beispiel') und invalid/<code>/ mit expected.json (code, file, line) für alle 12 Fehlercodes.
- Kennung: ein Absatz, der mit 'Format:' beginnt und 'backlog format version 2' enthält (wie die Vorlage von Version 1).
