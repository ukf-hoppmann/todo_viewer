# NEW-ai-system-test — Spec: Systemtest und Prompt für Claude_Harness

Zu `STORY-104`. Der Vorschlag „im Gespräch“ ist kein Server-Zustand; der Test bildet das Gespräch durch zwei
getrennte Aufrufsfolgen nach (Vorschlag = nichts passiert; Zustimmung = Knoten wird angelegt).

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.

## Systemtest

Datei: `tests/implementation/system/server/test_harness_flow.py` oder, wenn sie dadurch zu lang wird, eine neue Datei
daneben mit demselben Aufbau (Server als Prozess, bedient über MCP wie vom Harness). Ablauf:

1. Projekt mit Themenbaum und einem Epic als Knoten vorbereiten (über die Tools).
2. `mindmap_get_tree` lesen; Item mit `mindmap_create_item_at_node` am passenden Knoten anlegen; `get_tree` zeigt es
   dort, Knoten „Geplant“.
3. Ein Item, das zu keinem Knoten passt: zuerst `backlog_create_item` ohne Knoten — es steht unter „Nicht
   zugeordnet“ und der Baum hat keinen neuen Knoten.
4. Nach der simulierten Zustimmung: `mindmap_create_node` (Parent gewählt), `mindmap_assign_item` — das Item hängt am
   neuen Knoten, „Nicht zugeordnet“ ist leer.
5. Zustimmung verweigert: ein weiteres Item bleibt unter „Nicht zugeordnet“, der Baum unverändert.

## Prompt für Claude_Harness

Zielgruppe: eine Sitzung im Repository von Claude_Harness (Skills, `todo`-Regeln). Der Prompt enthält:

- Ziel: Wer ein Backlog-Item anlegt, ordnet es dem Themenbaum des Viewers zu; Knoten werden nur nach Zustimmung des
  Owners angelegt.
- Die Regel (aus der Spec der Task „MCP-Tools nennen die Regel“, im Wortlaut, den die Beschreibungen jetzt tragen).
- Die Werkzeuge mit den Namen, die der Viewer ausgibt (`tools/list` prüfen).
- Wo sie hinkommen könnte (Skill `todo`, Abschnitt „Working rules“; Hinweis zu neuen Items) und dass der Wortlaut dort
  zur Sprache des Skills passen muss.
- Für Dateimodus (Cloud-Sitzungen ohne Server): noch nicht beschrieben; der Mindmap-Spiegel (`STORY-105`) bringt das
  nach. Der Prompt sagt das und bittet nur um die Regel für den API-Modus.

Ablage wie bei `area-prompts`: als `<ID>_spec_prompt-harness.md` neben dieser Spec, am Ende der Sitzung vollständig
im Text an den Owner.
