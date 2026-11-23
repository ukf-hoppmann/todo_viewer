# NEW-node-create-server — Spec: Item oder Memo aus einem Knoten anlegen (Server)

Zu `STORY-103` (Entscheidungen in `STORY-103_notes.md`): Der Typ wird nie aus der Ebene abgeleitet; Mensch oder KI
legt ihn je Knoten fest. Ein Knoten kann ein Item oder ein Memo werden; der Knoten bleibt stehen.

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.

## Operationen (Plugin `mindmap`)

Nach dem Muster der vorhandenen Operationen in `server/src/viewer/plugins/mindmap/application/operations.py`
(Dataclass für Eingabe und Ausgabe, `Operation(…)`, `HttpBinding`; MCP-Tool `mindmap_<name>`).

- `create_item_at_node`
  - Eingabe: `node` (uid oder Label), `type` (`Epic`, `Story`, `Task`), `fields` (dieselben Felder wie
    `backlog_create_item`: `title`, `goal`, `completion_criteria`, optional `priority`, `required_for_parent`,
    `summary`, `parent` (uid), `dependencies` (uids)), `project` (nur wenn `node` ein Label ist), `tree`
    (optional, wie bei `get_node`).
  - Standardwerte: fehlt `title` → Titel des Knotens; fehlt `goal` → Text des Knotens, falls vorhanden. Sonst
    keine; `completion_criteria` müssen kommen (der Knoten hat keine).
  - Ablauf: Knoten prüfen (existiert, nicht im Papierkorb), Item über das Plugin `backlog` anlegen, danach mit
    `AssignmentService.assign_item` (`application/assignments.py`) an den Knoten hängen. Zwei Transaktionen
    genügen; scheitert die Zuordnung, bleibt das Item ohne Knoten bestehen und der Fehler nennt es
    (`details.created`), kein Rückbau.
  - Ausgabe: das angelegte Item (`uid`, `label`, `type`, `title`) und der Knoten wie `get_node` (mit Zustand).
- `create_memo_at_node`
  - Eingabe: `node`, `fields` (wie `memos_create_memo`: `summary`, `body`, `topic`, `review_at`, `trigger_mode`),
    `project`.
  - Standardwerte: `summary` = Titel des Knotens, `body` = Text des Knotens.
  - Ablauf: Memo über das Plugin `memos` anlegen, dann `AssignmentService.link_memo`.
  - Ausgabe: das Memo (`uid`, `label`, `summary`) und der Knoten.

## Aufbau

- Neue Ports in `application/ports.py`: `BacklogWriter.create_item(project_uid, type_, fields) -> str` und
  `MemoWriter.create_memo(project_uid, fields) -> str`. Adapter in `infrastructure/` (wie
  `backlog_gateway.py`, der `services.repository` des Plugins `backlog` benutzt): `ServicesBacklogWriter` ruft
  `services.editing.create_item(project_uid, type_, fields)`; `ServicesMemoWriter` ruft `services.memos.create(
  project_uid, fields)` des Plugins `memos`. Vorbild für beide ist `memos/infrastructure/backlog_gateway.py`
  (`create_item`).
- `plugin.py` des Plugins `mindmap`: `requires=("workspace", "backlog", "memos")`, die Dienste aus
  `context.required` holen und den Anwendungsfall in `MindmapServices` verdrahten; `server/pyproject.toml`
  (`[tool.importlinter]`) so ergänzen, dass `mindmap` die öffentliche Schnittstelle von `memos` benutzen darf
  (`memos` benötigt `backlog`, nicht `mindmap`: kein Zyklus). Zusammengesetzt wird nur in
  `server/src/viewer/app/composition.py` (Reihenfolge der Plugins prüfen).
- Fehler als `DomainError` mit stabilem `code`; gesprochen wird deutsch wie in den übrigen Meldungen.
- Ereignisse: Zuordnen und Verlinken senden die vorhandenen (`mindmap.node.changed`, `backlog.item.changed`,
  Memo-Ereignis); die Oberfläche lädt darüber neu.

## Tests

- Unit: `tests/implementation/unit/server/plugins/mindmap/test_create_at_node.py` mit Fakes der neuen Ports (Standard
  für Titel und Ziel; Pflicht der Kriterien; Papierkorb-Knoten; Fehler beim Zuordnen nennt das Item).
- Integration: `tests/implementation/integration/server/plugins/mindmap/test_mindmap_create_at_node.py` (echte Plugins,
  Muster: `test_mindmap_assignment.py`): Item anlegen → Knoten hat Zustand „Geplant“ (`get_tree`); Memo anlegen →
  Zustand bleibt „Idee“; Standardwerte; Knoten eines anderen Projekts; beide Tools stehen in der MCP-Tool-Liste.
- `scripts/gen-api.sh` ausführen; `test_openapi_types.py` prüft die Typen.

## Nicht Teil

Ganze Äste (nächste Task), Oberfläche, die Regel für die KI.
