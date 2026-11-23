# NEW-branch-transfer-server — Spec: Ast mit Vorschau überführen (Server)

Zu `STORY-103`. Der Owner hat entschieden (`STORY-103_notes.md`): kein Automatismus nach Ebene oder Tiefe; jeder Ast
wird einzeln entschieden; ein tiefer Knoten kann ein eigenes Epic werden; die Grenze von drei Ebenen gilt für das
Backlog, nicht für die Tiefe in der Map; Kinder eines Astes können Abhängigkeiten oder Parent-Child sein.

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.

## Plan

Eingabe beider Operationen: `root` (der oberste Knoten des Astes, uid oder Label), `tree` (optional), `project`
(nur bei Labels) und `entries`, eine Liste. Ein Eintrag:

| Feld | Bedeutung |
|---|---|
| `node` | Knoten des Astes (`root` oder einer seiner Nachfahren in diesem Baum) |
| `kind` | `item`, `memo` oder `skip`; ein Knoten ohne Eintrag wird wie `skip` behandelt |
| `type` | bei `item`: `Epic`, `Story`, `Task` |
| `title`, `goal`, `completion_criteria`, `summary`, `priority` | Felder des Items; Standard wie in `create_item_at_node` (Titel und Text des Knotens) |
| `memo` | bei `memo`: `summary`, `body` (Standard Titel und Text des Knotens) |
| `parent` | optional: ein anderer Knoten des Plans (das neue Item wird sein Kind) oder ein vorhandenes Item (uid oder Label) |
| `depends_on` | optional: Liste von Knoten des Plans oder vorhandenen Items, von denen das neue Item abhängt |

Ein Knoten kommt höchstens einmal vor. Ein Memo hat weder Parent noch Abhängigkeiten und kann selbst kein Ziel von
`parent` oder `depends_on` sein.

## Vorschau

`preview_branch_transfer` gibt je Eintrag `node`, `ok` und `problems` (Liste von `{code, message}`) zurück, dazu
`problems` für den ganzen Plan (z. B. Zyklen) und die Reihenfolge, in der angelegt würde. Mindestens diese Codes:
`node_not_in_branch`, `node_duplicate`, `invalid_type`, `goal_missing`, `criteria_missing`,
`parent_type_not_allowed`, `parent_is_memo`, `parent_not_found`, `parent_closed`, `dependency_cycle`,
`depends_on_not_found`. Die Typ-, Parent-, Zyklus- und Abschlussregeln stammen aus dem Backlog.

Dafür bekommt das Plugin `backlog` (Datei `application/editing.py`, öffentlicher Dienst `services.editing`) eine
nicht schreibende Prüfung `check_new_items(project_uid, planned)`: Sie baut die geplanten Items mit
`build_new_item` (Platzhalter-Uids, Beziehungen untereinander) und prüft sie mit denselben Regeln wie `create_item`
(`self._rules.check_change(before, [*before, *planned])`, Regeln in `domain/lifecycle.py`). `check_change` wirft nur
die *erste* Verletzung (`LifecycleViolation`); die Vorschau braucht alle Probleme je Eintrag. Darum entsteht in
`domain/lifecycle.py` eine sammelnde Variante derselben Regeln (eine Implementierung, `check_change` ruft sie auf und
wirft die erste; keine zweite Kopie der Regeln). Das Ergebnis der Prüfung ist eine Liste von Problemen je Eintrag.
Die Mindmap ruft sie über einen neuen Port auf (Adapter wie `ServicesBacklogItems`, ohne Import von Code des
Plugins `backlog`) und baut die Regeln nicht nach (Architektur §1: was mehrere Plugins brauchen, liegt an einer
Stelle).

## Überführen

`transfer_branch` prüft zuerst genau wie die Vorschau und bricht mit `transfer_blocked` (Probleme in `details`) ab,
wenn es eines gibt. Sonst legt es die Einträge in der Reihenfolge der Beziehungen an (Parents und Abhängigkeiten
vor ihren Nachfahren), Items über denselben Weg wie `create_item_at_node`, Memos wie `create_memo_at_node`, jeweils
mit dem Knoten verbunden. Die Uids der neu angelegten Items ersetzen die Verweise auf Knoten des Plans. Ergebnis:
je Eintrag `created` (mit Label) oder `failed` (mit Fehler), `skipped` für die übrigen; scheitert ein Eintrag,
folgen alle, die von ihm abhängen, als `not_attempted`; Angelegtes bleibt (kein Rückbau).

Die Knoten bleiben unverändert; ihr Zustand ergibt sich aus den neuen Items (`get_tree`).

## Tests

- Unit: `tests/implementation/unit/server/plugins/mindmap/test_branch_transfer.py` (Plan prüfen, Reihenfolge,
  Codes, Teilfehler) mit Fakes der Ports; für `check_new_items` ein Test in
  `tests/implementation/unit/server/plugins/backlog/`.
- Integration: `tests/implementation/integration/server/plugins/mindmap/test_mindmap_transfer.py`: Epic → Story →
  Task aus einem Ast; ein Knoten in Tiefe 5 als eigenes Epic; Abhängigkeit statt Parent; Memo im Plan; Epic unter
  Task wird in der Vorschau gemeldet und nichts entsteht; zweiter Lauf desselben Plans legt Doppelte an (kein
  Schutz; der Aufrufer prüft über die Vorschau, dass die Knoten noch keine Items haben, falls er das will).
- Systemtest: `tests/implementation/system/server/test_harness_flow.py` bekommt einen Abschnitt „Ast überführen“
  über MCP.

## Nicht Teil

Oberfläche (übernächste Task), die Regel für die KI.
