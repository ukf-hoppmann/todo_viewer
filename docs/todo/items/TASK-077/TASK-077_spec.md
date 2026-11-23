# TASK-077 — Spec: Regel für die KI in den MCP-Tool-Beschreibungen

Zu `STORY-104` (Entscheidungen in `STORY-104_notes.md`): Vorschläge laufen im Gespräch; die Regel steht in den
MCP-Tool-Beschreibungen des Viewers (wirkt sofort für jede KI) und wird zusätzlich als Skill-Regel an Claude_Harness
übergeben (der Prompt dafür ist Teil der nächsten Task).

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.

## Regel (Inhalt der Beschreibungen)

1. Legst du ein Item an, überlege, zu welchem Thema es gehört: lies den Themenbaum des Projekts
   (`mindmap_get_tree`).
2. Passt ein Knoten, lege das Item an ihm an (`mindmap_create_item_at_node`) oder ordne ein vorhandenes zu
   (`mindmap_assign_item`).
3. Passt keiner, schlage dem Owner im Gespräch einen Knoten oder Unterknoten vor (Titel, Ort im Baum). Lege ihn
   (`mindmap_create_node`) erst an, wenn der Owner zugestimmt hat. Erfinde keine Themen ohne Zustimmung.
4. Stimmt der Owner nicht zu oder ist er nicht erreichbar, lege das Item ohne Knoten an (`backlog_create_item`); es
   steht dann unter „Nicht zugeordnet“.
5. Ein Epic ist meist selbst ein Knoten; Stories und Tasks darunter erben seinen Knoten (ein eigens zugeordnetes Item
   zieht seine Kinder mit).

Der genaue Wortlaut wird in der Task geschrieben und bleibt kurz (die Beschreibungen stehen im Kontext jeder
Sitzung).

## Umfang

- Eine Konstante für den gemeinsamen Satz an einer Stelle im Plugin `mindmap`
  (`server/src/viewer/plugins/mindmap/application/operations.py` oder eine kleine Datei daneben) und deren
  Verwendung in den Beschreibungen von `get_tree`, `create_node`, `assign_item`, `create_item_at_node`.
- `backlog_create_item` gehört dem Plugin `backlog`, das die Mindmap nicht kennt (Architektur §1). Seine
  Beschreibung enthält darum nur einen Hinweis ohne Namen der Mindmap-Werkzeuge: „Hat das Projekt einen Themenbaum
  (MCP-Tools `mindmap_…`), ordne das neue Item einem Knoten zu; siehe `mindmap_create_item_at_node`.“ Der Hinweis
  steht dort als Text, nicht als Import.
- Kein neues Werkzeug, kein neuer Zustand, keine Oberfläche.

## Tests

- Unit: `tests/implementation/unit/server/plugins/mindmap/test_tool_descriptions.py`: die Beschreibungen der
  genannten Operationen enthalten die Schlüsselaussagen; die Beschreibung von `backlog_create_item` enthält den
  Hinweis (Prüfung über die Operationstabellen `OPERATIONS` der Plugins).
- Der Systemtest folgt in der nächsten Task.
