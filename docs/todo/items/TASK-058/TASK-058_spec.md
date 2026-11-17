# TASK-058 — Spec: Fokus auf einen Knoten und die Aktionen „Gehe hin“, „Erstelle“, „Anker“

Regeln: `STORY-101_spec.md` (Abschnitte „Fokus“ und „Aktionen am Item“); Konzept: `EPIC-008_spec.md`. Nur Client.

## Umfang

- Fokus in der Adresse: `mindmap/main?focus=<uid>`. Die Seite liest und setzt den Parameter (Query-Parameter der
  Route; die Routen kennen sonst keine Parameter). Ohne oder mit unbekanntem Fokus gilt die Projektwurzel.
- Pfad von der Projektwurzel bis zum Fokus über der Map; ein Klick auf einen Eintrag setzt den Fokus dorthin. Am
  Knoten (Menü oder Aktion) gibt es „Als Wurzel öffnen“.
- Die Map zeigt nur den Ast ab dem Fokus; die Tiefe zählt ab dem Fokus (zwei Ebenen darunter offen, solange nichts
  gefaltet wurde). Gefaltet wird weiter je Knoten im UI-State.
- Drei Aktionen im Item-Detail (`ItemNodeSection`, Slot `backlog.item-detail`):
  - „Gehe hin“: Navigation zu `mindmap/main?focus=<wirksamer Knoten>`; ohne Knoten die Wurzel. Gehört das Item zu
    einem ausgeblendeten Projekt, wird dieses eingeblendet und als gezeigtes Projekt markiert (über die
    öffentliche API des Plugins `workspace`; kein Zugriff auf dessen Interna).
  - „Erstelle“: `createNode` unter dem wirksamen Knoten (sonst unter der Wurzel) mit dem Titel des Items, dann
    `assignItem` mit `replace`. Fehler beim Anlegen oder Zuordnen erscheinen im Abschnitt.
  - „Anker“: nur wenn `explicit` (das Item hängt eigens an einem Knoten); öffnet die Map mit diesem Knoten als Wurzel.
- Nichts davon wird für ein Item im Papierkorb angeboten (wie der übrige Abschnitt).

## Schnittstellen und Dateien

- `client/src/plugins/mindmap/domain/tree.ts`: neue reine Funktionen `focusPath(rootId, nodes, focusId)` (Pfad als
  Liste von Knoten-IDs ab der Wurzel, `null` bei unbekanntem Fokus) und `parentForNewNode(effectiveNodeUid, rootId)`;
  `visibleNodes` bekommt eine Wurzel für den Fokus (Tiefe ab dort).
- `pages/MindmapPage.tsx`, `ItemNodeSection.tsx`, `testIds.ts` (neue IDs `mindmap.<element>` für Pfad, Pfadeintrag,
  „Als Wurzel öffnen“, drei Item-Aktionen), `locales/de.json` und `en.json`.
- Ein neuer Navigationsbaustein (Hook oder Funktion, die die Adresse baut) liegt im Plugin `mindmap` und wird von
  `ItemNodeSection` und der Seite gemeinsam benutzt; nichts davon in `core`.

## Nicht Teil

Gesamtansicht (`TASK-059`), Anordnung (`TASK-060`), Abhängigkeiten (`TASK-061`), freie Maps (`STORY-102`).

## Tests

Vitest und Testing Library unter `tests/implementation/unit/client/plugins/mindmap/`: Domain-Funktionen zuerst
(`tree.test.ts`), danach `MindmapPage.test.tsx` (Fokus aus der Adresse, Pfad, Klick auf den Pfad, „Als Wurzel
öffnen“) und `ItemNodeSection.test.tsx` (drei Aktionen, „Anker“ nur mit `explicit`, Fehlerfall von „Erstelle“).
Selektoren nur über `data-testid`. Die Architekturregeln des Scopes `client` gelten (Layer, `index.ts`, Test-IDs).
Danach Techdocs (Abschnitt Plugin `mindmap`) auf den neuen Stand bringen.
