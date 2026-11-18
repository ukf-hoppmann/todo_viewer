# TASK-061 — Spec: Abhängigkeiten zwischen Themen

Regeln: `STORY-101_spec.md` (Abschnitt „Abhängigkeiten“). Dieser Task berührt Server und Client; er ist der größte der
Story. Für das Ticket reicht „reine Funktion getestet“; zusätzlich sind Server-Tests und UI-Tests Teil des Tasks.

## Umfang

### Server (zuerst, Test zuerst)

- Port `BacklogItems` (`application/ports.py`): `BacklogItem` bekommt `dependencies` (UIDs der Items, die es braucht).
  `ServicesBacklogItems` (`infrastructure/backlog_gateway.py`) reicht sie aus dem Repository des Plugins `backlog`
  durch, ohne dessen Code zu importieren.
- Domain (`domain/`): reine Funktion, die aus den Items, ihren wirksamen Knoten und den Abhängigkeiten die Linien
  bildet: Linie von dem Knoten, der das *benötigte* Item trägt, zu dem Knoten des *abhängigen* Items, mit Anzahl.
  Zusammengefasst wird je Knotenpaar; Items im Papierkorb, Items ohne wirksamen Knoten und Paare im selben Knoten
  fallen weg. Nur Abhängigkeiten innerhalb des Projekts des Baums (Owner-Entscheidung 2026-11-17).
- `TreeOut` (`application/operations.py`) bekommt `links: list[LinkOut]` (`from_node`, `to_node`, `count`); bei
  Statusfilter gelten dieselben zählenden Items wie bei den Zahlen. Das OpenAPI-Schema wird geändert, der Test
  `test_openapi_types.py` verlangt die Neuerzeugung von `client/src/shared/api/schema.d.ts` (nicht von Hand).

### Client

- `domain/tree.ts`: reine Funktion `liftLinks(links, shownIds, parentOf)`: Linien enden am sichtbaren Vorfahren eines
  gefalteten oder ausgeblendeten Knotens; Linien, die dadurch zwischen demselben Knoten verlaufen, entfallen;
  gleiche Paare werden wieder zusammengefasst. Test zuerst.
- Darstellung: gestrichelte Linien in einer eigenen Farbe, beschriftet mit der Anzahl, mit Pfeilspitze am abhängigen
  Thema; sie verdecken die Baumkanten nicht und sind nicht anklickbar.
- Schalter in einer Sektion der Seitenleiste; UI-State `showDependencies` (Standard `false`).
- In der Gesamtansicht (`TASK-059`) werden die Linien je Projekt gezeichnet; es gibt keine Linien zwischen Projekten.

## Schnittstellen und Dateien

`server/src/viewer/plugins/mindmap/{application/ports.py,application/operations.py,application/service.py,domain/,infrastructure/backlog_gateway.py}`,
`client/src/shared/api/schema.d.ts` (generiert), `client/src/plugins/mindmap/{domain/tree.ts,pages/MindmapPage.tsx,state.ts,testIds.ts,locales/*}`.
Die Regeln der Scopes `server` und `client` gelten (Layer, Operationen, Fehlercodes, Test-IDs).

## Nicht Teil

Linien über Projektgrenzen, Linien zwischen Items (der Graph im Backlog bleibt davon unberührt).

## Tests

Server: Unit-Tests der Domain-Funktion (`tests/implementation/unit/server/plugins/mindmap/`), ein Integrationstest
des Endpunkts (`tests/implementation/integration/server/plugins/mindmap/`). Client: `tree.test.ts` für `liftLinks`,
`MindmapPage.test.tsx` für Schalter (Standard aus, Zustand bleibt) und Linien. Techdocs (Schnittstellen und
Plugin `mindmap`) nachziehen.
