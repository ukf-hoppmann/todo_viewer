# TASK-058 — Mindmap: Fokus auf einen Knoten und die Aktionen „Gehe hin“, „Erstelle“, „Anker“ am Item

## State

- Goal/Status: Abgeschlossen: vom Owner bestätigt und nach `todo_mindmap` gemergt (2026-11-17).
- Next step: Nächster Task der Story: `TASK-060` (runde Anordnung).
- Open:
  - Lint: fünf Fehler in `core/ui-state/usePersistentState.ts` (react-hooks/refs) bestanden schon vor dem Task; `npm run build` bricht daran ab, `vite build` läuft (2026-11-17)
- Decided:
  - Der Fokus steht als `?focus=<uid>` in der Adresse; die Routen kennen sonst keine Parameter (2026-11-17)
  - „Gehe hin“ blendet ein ausgeblendetes Projekt des Items ein und markiert es (2026-11-17)
  - Schalter und Aktionen folgen `STORY-101_spec.md` (2026-11-17)
  - Der Fokusknoten verhält sich wie jeder andere Knoten (Umbenennen, Detail, Anlegen, Papierkorb); nur die Tiefe zählt ab ihm; wird er gelöscht, gilt die Projektwurzel (2026-11-17)
  - „Anker“ blendet ein ausgeblendetes Projekt des Items ebenfalls ein und markiert es, wie „Gehe hin“ (2026-11-17)
- References: Spec `TASK-058_spec.md`; Story-Spec `STORY-101_spec.md`; Notizen `STORY-101`

State confirmed after entry 2026-11-17 — Bestätigung (4f5c86a3f22d)

## 2026-11-17 — Anlage aus der Planung der Story

### Discussed

- Planung der Story `STORY-101` mit dem Owner; Aufbau und Aufteilung stehen in deren Notizen.
- Ein Fokus in der Adresse braucht einen Query-Parameter, weil die Routen `<owner>/<name>` keine Pfadparameter haben.

### Decided

- Fokus als Query-Parameter `focus`
- „Gehe hin“ blendet ein ausgeblendetes Projekt ein und markiert es (Owner, 2026-11-17)

### Open

- Nichts offen.

## 2026-11-17 — Plan und Klärung offener Punkte

### Discussed

- Plan mit sechs Sections vorgelegt: Domain (Test zuerst), Navigationsbaustein, Seite mit Pfad, Item-Aktionen, Techdocs, Integration.
- Fokusknoten: wie jeder andere Knoten (empfohlen; wenig Sonderfälle) oder wurzelartig ohne Papierkorb und Detail.
- „Anker“ bei ausgeblendetem Projekt: einblenden und markieren (empfohlen, sonst Fokus ohne gezeigtes Projekt) oder nur navigieren.

### Decided

- Fokusknoten wie jeder andere Knoten (Owner)
- „Anker“ blendet das Projekt ein und markiert es, wie „Gehe hin“ (Owner)

### Open

- Freigabe des Plans durch den Owner

## 2026-11-17 — Umsetzung

### Discussed

- Plan vom Owner freigegeben (Ja); sechs Sections: Domain (Test zuerst), Navigationsbaustein, Seite mit Pfad, Item-Aktionen, Techdocs, Integration.
- Der Fokus gilt erst, wenn der Baum geladen ist und der Knoten darin steht; sonst zeigt die Seite die Projektwurzel (kein Aufblitzen der Wurzel beim Laden).
- Der Testhelfer `renderWorkspace` bekam `initialEntries` und eine Ortssonde (`LocationProbe`, `locationTestId`, eigene Dateien wegen der Lint-Regel `react-refresh`).

### Decided

- Navigationsbaustein `navigation.ts` im Plugin (`mapAddress`, `useMapNavigation`); nichts in `core`.
- „Gehe hin“ und „Anker“ blenden ein ausgeblendetes Projekt ein und markieren es über `useProjectSelection`.
- „Erstelle“ sperrt sich während des Anlegens, damit kein Knoten doppelt entsteht.

### Open

- Lint-Altlast in `usePersistentState.ts`, nicht Teil dieses Tasks.
- Bestätigung durch den Owner, danach Merge.

## 2026-11-17 — Bestätigung

### Decided

- Der Owner hat den Task bestätigt (`Completed`) und den Merge von `claude/task-058-mindmap-fokus` nach `todo_mindmap` verlangt; kein Release, keine Versionserhöhung.
