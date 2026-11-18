# TASK-059 — Spec: Gesamtansicht mit gemeinsamer Wurzel

Regeln: `STORY-101_spec.md` (Abschnitt „Gesamtansicht“). Baut auf `TASK-058` auf (Fokus, Pfad). Nur Client; der Server
bleibt unverändert.

## Umfang

- Schalter Einzelansicht / Gesamtansicht in einer Sektion der Seitenleiste (`core.sidebar-sections`,
  `when: ["mindmap/main"]`). Die Wahl liegt im UI-State (`view`, Eigentümer `mindmap`).
- Gesamtansicht: eine gemeinsame Wurzel (kein Projekt, kein Datensatz), darunter die gewählten sichtbaren Projekte
  als erste Knoten, jedes mit seinem Baum. Projekte hinzu- und wegschalten wirkt sofort (die Projektauswahl kommt aus
  `useProjectSelection`).
- Summen der gemeinsamen Wurzel: Anzahl und erledigt addieren die Projekte (jedes Item gehört zu einem Projekt und
  zählt einmal; Items ohne Knoten zählen nicht mit, die Projektsumme ist die der obersten Knoten); der Zustand folgt der Regel aus `STORY-100_spec.md` über die Zustände der Projektknoten. Die
  Projektknoten tragen die Summen ihrer Bäume wie bisher die Projektwurzel.
- An der gemeinsamen Wurzel gibt es kein Hinzufügen, Umhängen oder Zuordnen; Ziehen eines Items oder Knotens auf sie
  wird nicht angeboten. Fokus und Pfad aus `TASK-058` gelten (der Pfad beginnt bei der gemeinsamen Wurzel).
- Die Seitenansicht „Nicht zugeordnet“ gilt je Projekt. In der Gesamtansicht zeigt sie die
  Items des markierten Projekts, sonst ist sie aus (Owner 2026-11-18).

## Schnittstellen und Dateien

- Daten: ein neuer Endpunkt `getTrees` in `api.ts` (RTK Query, `queryFn` mit paralleler Abfrage von
  `mindmap/trees/{project}` für alle gewählten Projekte; Tag `Tree`), damit keine Hooks in Schleifen entstehen.
- `domain/tree.ts`: reine Funktion `combinedTree(projects, trees)` (Knoten mit `parent_uid` der Projektknoten,
  Summen, Zustand); Test zuerst.
- `pages/MindmapPage.tsx` (Wurzelwahl je Ansicht), neue Sektion `ViewSwitch` oder Erweiterung von `MapFilters`,
  `state.ts`, `testIds.ts`, `locales/*`.

## Nicht Teil

Anordnung (`TASK-060`), Abhängigkeiten über Projektgrenzen (nicht vorgesehen), freie Maps (`STORY-102`).

## Tests

`tree.test.ts` (Summen ohne Doppelzählung, Zustand, leere Projekte), `MindmapPage.test.tsx` (Umschalten, Projekt
hinzu und weg, Wurzel nimmt nichts an), Test der Sektion. Selektoren nur über `data-testid`. Techdocs
nachziehen.
