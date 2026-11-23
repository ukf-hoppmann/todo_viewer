# TASK-082 — Spec: Abschluss des Mindmap-Spiegels

Zu `STORY-105`; baut auf den Tasks „Dateiformat und Codec“, „Teilnehmer für Knoten und Bäume“ und „Zuordnungen,
Dokumente …“ auf.

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.
Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/client.md`. Tests und Befehle: `tests/README.md`; Client-Tests unter `tests/implementation/unit/client/…` (Vitest, Testing Library), Hilfen unter `tests/helpers/client/`. Am Ende laufen `cd client && npx tsc -b && npm run lint` und alle Client-Tests grün.

## Sync-Dialog

`client/src/plugins/workspace/SyncDialog.tsx` zeigt Übertragungen und Konflikte als `{label ?? kind}`; der Dialog ist
allgemein. Für die Mindmap prüfen und ergänzen: die `kind`-Werte `mindmap.node`, `mindmap.tree`, `mindmap.document` (und
ihre Felder: Titel, Text, Markierung, Ordnung) bekommen lesbare Namen und Feldnamen in `workspace/locales/de.json`
und `en.json`; ein Konflikt am Baum zeigt die Ordnung als Liste (Diff), kein JSON. Wo der Dialog Kontext zu Dokumenten
zeigt (`sync.context.*`), ergänzt die Mindmap „Notiz zu Knoten …“. Test:
`tests/implementation/unit/client/plugins/workspace/`.

## Systemtest „Cloud-Sitzung“

Datei: neu `tests/implementation/system/server/test_mindmap_mirror_flow.py` (Aufbau wie `test_harness_flow.py`: Server
als Prozess, MCP). Ablauf:

1. Projekt mit Spiegel-Ordner anlegen, Mindmap über MCP füllen, Sync in die Dateien.
2. Die Dateien so ändern, wie es eine Cloud-Sitzung täte (nur Textdateien bearbeiten): in einer freien Map einen
   neuen Knoten mit Platzhalter anlegen, einen Ast in der Baumdatei umhängen, einen Ast in die Baumdatei einer
   anderen Map übertragen (Verweise statt Kopie), ein Item in `Items:` eines Knotens eintragen.
3. Sync Dateien → Datenbank; das Ergebnis (`mindmap_get_tree`, `mindmap_get_node_content`) entspricht dem, was die
   gleichen Schritte über die API ergäben (ein zweiter, identischer Ablauf über MCP als Vergleich).
4. Ein Konflikt (derselbe Knoten auf beiden Seiten geändert) wird gemeldet, nichts überschrieben.

## Doku

- `docs/techdocs/neubau-server.md`: Abschnitt zum Plugin `mindmap` um Spiegel, Teilnehmer, Dateiformat ergänzen.
- `docs/techdocs/interfaces.md`: Format ist seit der ersten Task beschrieben; die Fehlercodes und die Tabelle der
  Spiegel-Dateien aktuell halten.
- `README.md` und `docs/techdocs/operations.md`: nennen, dass `mindmap/` im Spiegel-Ordner liegt (falls Ordnerstruktur
  dokumentiert ist).
- `docs/todo/items/EPIC-008/EPIC-008_spec.md`: der Absatz zum Markdown-Spiegel („mitgeplant, nicht Pflicht“) nennt den
  umgesetzten Stand.

## Prompt für Claude_Harness

Zielgruppe: Sitzung im Repository von Claude_Harness. Inhalt: Cloud-Sitzungen arbeiten im Datei-Modus ohne Server;
sie sollen die Mindmap über die Dateien nutzen können. Der Prompt beschreibt (mit Verweis auf
`docs/techdocs/interfaces.md`, „Mindmap-Dateien (Format Version 1)“, das der Owner mitgibt oder einfügt):

- die Dateien (`mindmap/NODE-nnn.md`, `project.md`, `maps/<name>.md`, Dokumente) und ihre Felder,
- die Regeln: Knoteninhalt steht einmal, Bäume verweisen; Platzhalter `new-<kurzname>` für Neues; ein Item an höchstens
  einem Knoten; Äste umhängen heißt die Zeilen in den Baumdateien verschieben, nicht Knoten kopieren,
- die Regel für die KI aus `STORY-104` (Knoten zuordnen, nur nach Zustimmung anlegen) für den Datei-Modus,
- was Claude_Harness in `todo`-Skill, `format.md`, Prüfskript (`backlog.py`) und Vorlagen ergänzen soll
  (die Prüfskripte dürfen `mindmap/` nicht als unbekannte Dateien melden).

Ablage: `<ID>_spec_prompt-harness.md` neben dieser Spec; am Ende der Sitzung vollständig im Text an den Owner.
