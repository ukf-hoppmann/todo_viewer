# TASK-076 — Oberfläche: einen Ast mit Vorschau ins Backlog überführen

## State

- Goal/Status: Umgesetzt und geprüft (2026-11-24): Dialog „Ast überführen“ mit Vorschau am Knoten, Ergebnis je Knoten; Typen, Lint und Tests grün; wartet auf die Abnahme des Owners.
- Next step: Abnahme durch den Owner; danach ist die Story STORY-103 auf ihre Kriterien zu prüfen.
- Open:
  - Nichts offen (2026-11-24)
- Decided:
  - Die Beziehung wird je Knoten gewählt (Kind von, hängt ab von, keine); es gibt keine Vorbelegung nach Ebene (Owner: kein Automatismus; die Gestaltung der Wahl ist Zuschnitt) (2026-11-23)
  - Die Beziehungswahl im Dialog (Kind von, hängt ab von, keine; keine Vorbelegung) ist vom Owner bestätigt (2026-11-23)
  - Ziel der Beziehung: andere Knoten, die im Plan ein Item werden, und vorhandene Items des Projekts; Memos und übersprungene Knoten werden nicht angeboten (2026-11-24)
  - Die Vorschau ist eine entprellte Abfrage (250 ms); „Überführen“ ist nur bei nicht leerem Plan und einer Vorschau zum aktuellen Plan ohne Probleme möglich (2026-11-24)
  - Beziehungen zu einem Knoten, der kein Item mehr wird, fallen beim Bauen des Plans weg (2026-11-24)
- References: Spec `TASK-076_spec.md`; Story `STORY-103` (Notes mit den Entscheidungen des Owners); Abhängigkeiten: TASK-074, TASK-075; Code `client/src/plugins/mindmap/TransferBranchDialog.tsx`, `domain/transferPlan.ts`; Doku `docs/techdocs/neubau-client.md`

State confirmed after entry 2026-11-24 — Umsetzung (9a4859321f41)

## 2026-11-23 — Zuschnitt aus der Planung von STORY-103

### Discussed

- Die Task ist ein Zuschnitt der Story STORY-103 nach den Besprechungen mit dem Owner; Optionen, Gründe und
  verworfene Wege stehen in `STORY-103_notes.md`.
- Die Spec wurde so geschrieben, dass eine Session ohne den Planungsverlauf umsetzen kann: Dateien und Symbole sind
  genannt, Entscheidungen stehen fest.

### Decided

- Die Beziehung wird je Knoten gewählt (Kind von, hängt ab von, keine); es gibt keine Vorbelegung nach Ebene (Owner: kein Automatismus; die Gestaltung der Wahl ist Zuschnitt)

### Open

- Nichts.

## 2026-11-23 — Beziehungswahl bestätigt

### Discussed

- Der Owner hat die Gestaltung der Beziehungswahl in der Spec geprüft.

### Decided

- Sie bleibt wie in der Spec: „Kind von“, „hängt ab von“ (mehrere) oder keine, ohne Vorbelegung.

### Open

- Nichts.

## 2026-11-24 — Umsetzung

### Discussed

- Umgesetzt nach der Spec: Zeilen des Astes und Plan als reine Funktionen in `domain/transferPlan.ts` (Test zuerst), Vorschau und Überführen in `api.ts`, Dialog `TransferBranchDialog.tsx`, Menüeintrag „Ast überführen …“, Texte in de und en.
- Gestaltung im Rahmen der Spec: Der Ast steht als eingerückte Liste (Tiefe aus der Position im Ast) statt im gemeinsamen `TreeView`, weil jede Zeile Eingabefelder trägt, die `TreeView` nicht vorsieht. Das Ziel „Kind von“ und „Hängt ab von“ wählt der vorhandene `EntityPicker`; dafür exportiert `backlog` jetzt `useListItemsQuery` und `IndexItem` (öffentliche Schnittstelle, `mindmap` verlangt `backlog` schon).
- Fehlerfälle: Eine fehlgeschlagene Vorschau zeigt eine Warnung und sperrt „Überführen“; der Fehler beim Überführen (z. B. `transfer_blocked`) steht im Dialog.

### Decided

- Ziel der Beziehung: Knoten des Plans mit Art Item und vorhandene Items des Projekts.
- Vorschau als entprellte Abfrage; „Überführen“ nur ohne Probleme bei aktueller Vorschau.

### Open

- Nichts.
