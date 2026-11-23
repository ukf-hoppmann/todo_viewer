# NEW-mirror-format — Spec: Dateiformat und Codec des Mindmap-Spiegels

Zu `STORY-105` (nicht Pflicht für das Epic, vom Owner gewünscht). Entscheidung (`STORY-105_notes.md`): Inhalt einmal
je Knoten, Bäume als eigene Dateien mit Verweisen. Anforderungen aus `STORY-102`: mehrere Maps je Projekt mit Name
und Art; mehrfache Platzierungen je Knoten bei einmaligem Inhalt; entfernte Platzierungen und Papierkorb erkennbar;
eine Cloud-Sitzung füllt freie Maps und hängt Äste um oder überträgt sie mit denselben Regeln wie die API.

Rahmen: Architektur `docs/development/architecture.md` und `docs/development/architecture/server.md` (Schichten domain, application, infrastructure, api; Ports; Fehler als `DomainError`; Migrationen nur vorwärts, mit Backup). Tests und Befehle: `tests/README.md`; Unit-Tests unter `tests/implementation/unit/server/…`, Integrationstests unter `tests/implementation/integration/server/…`, feste Uhr, synthetische Daten. Neues Verhalten mit klarer Schnittstelle: Test zuerst schreiben und fehlschlagen sehen. Am Ende laufen `scripts/check-next.sh` und alle Tests grün.

## Format der Mindmap-Dateien (Version 1)

Alle Dateien liegen im Spiegel-Ordner des Projekts unter `mindmap/` (Muster des Codecs: `mindmap/**/*.md`). Vorbild
für Aufbau, Platzhalter und Dokumente ist der Memos-Spiegel (`server/src/viewer/plugins/memos/infrastructure/mirror/`
und `tests/fixtures/mirror-v2/valid/memos/`). Grundsatz (Owner, `STORY-105_notes.md`): **der Inhalt eines Knotens
steht genau einmal in einer Datei; jeder Baum ist eine eigene Datei, die nur Verweise auf Knoten in ihrer Ordnung
enthält.** Mehrfache Platzierungen sind Verweise, nie Kopien.

### Knoten: `mindmap/NODE-001.md`

```markdown
# NODE-001
Uid: 5d1c0c2e-7a53-4a0e-9f3b-0c9f8f6e1a01
Title: Mindmap-Ansichten
Mark: later
Deleted:
Items:
- Beispiel:STORY-101
Memos:
- Beispiel:MEMO-004

Freitext des Knotens (Text), beliebig lang, bis zum Dateiende.
```

- Kopfzeilen in fester Reihenfolge: `Uid`, `Title`, `Mark` (leer oder `later`/`discarded`), `Deleted` (leer oder
  Zeitpunkt UTC `…Z`, Format wie im Memos-Spiegel: `format_time`/`parse_time` in `memos/…/mirror/syntax.py`).
- `Items:` die eigens an den Knoten gehängten Items (Rolle `node` in `workspace_links`), `Memos:` die verlinkten
  Memos; Ziele als `Projekt:LABEL` (Projektname des eigenen Projekts darf wie im Memos-Spiegel auf das Label
  verkürzt gelesen werden). Ein Item steht höchstens bei einem Knoten (Regel von `STORY-100`); ein Memo darf bei
  mehreren stehen.
- Der Text nach der Leerzeile ist `Node.text`; ohne Text keine Leerzeile.
- Neue Knoten aus der Cloud: `mindmap/new-<kurzname>.md` mit `# NEW`, ohne `Uid`; der Sync vergibt `Uid` und Label
  `NODE-nnn`, die Datei wird umbenannt (wie `new-idee-export.md` bei Memos). Verweise auf Platzhalter in Baumdateien
  heißen `new-<kurzname>`.
- Dokumente eines Knotens: `NODE-001_notes.md`, `NODE-001_spec.md`, `NODE-001_spec_<thema>.md` (wie bei Memos).

### Baum: `mindmap/project.md` und `mindmap/maps/<name>.md`

```markdown
# Projekt
Format: mindmap format version 1
Uid: 9a2b…
Kind: project

- NODE-001
  - NODE-002
  - NODE-003
    - NODE-007
- NODE-004

Removed:
- NODE-010 parent NODE-001 position 2 group NODE-010
- NODE-011 parent NODE-010 position 0 group NODE-010
```

- `project.md` ist der Projektbaum (genau einer je Projekt, nicht löschbar). Freie Maps liegen in
  `mindmap/maps/<slug>.md` (Kopf zusätzlich `Name:` und `Deleted:` für den Papierkorb); der Dateiname ist der Name
  in `a-z0-9-` (Kollision: `-2`), gilt aber nur als Name der Datei: Identität ist `Uid`. Umbenennen benennt die
  Datei um.
- Die Liste gibt die Platzierungen: Einrückung um 2 Leerzeichen je Ebene, Reihenfolge = Stelle unter den
  Geschwistern, jeder Knoten in einem Baum höchstens einmal. Ein Knoten, der in mehreren Bäumen steht, steht in
  jedem dieser Bäume mit seinen dortigen Kindern; sein Inhalt steht nur in `NODE-nnn.md`.
- `Removed:` die gemerkten, entfernten Platzierungen (`RemovedPlacement`: Baum, Parent, Stelle, Gruppe `root_uid`);
  der Parent darf einen Knoten nennen, der nicht mehr im Baum steht.
- Ein neuer Baum aus der Cloud: `mindmap/maps/new-<kurzname>.md` mit `# NEW`, ohne `Uid`.

### Zuordnung zum Eintragsmodell

- Knoten = ein `MirrorEntry` (`kind` `mindmap.node`): Felder `title`, `text`, `mark`, `deleted`; Verweise `items`,
  `memos`. Dokument = `kind` `mindmap.document` (wie `memos.document`: `uid` = `<Knoten-uid>/<notes|spec|spec_…>`).
- Baum = ein `MirrorEntry` (`kind` `mindmap.tree`): Felder `tree_kind`, `name`, `deleted`, die Ordnung und die
  entfernten Platzierungen. Damit Platzhalter und Label-Wechsel der Knoten greifen, stehen die Knoten der Ordnung als
  Verweise (`refs`) in der Reihenfolge einer Tiefensuche, die Tiefen daneben in `fields`; entfernte Platzierungen
  analog. Das ist der Vorschlag der Spec; wer die Task umsetzt, darf eine gleichwertige Darstellung wählen, wenn die
  Golden-Files und der Sync-Test (Task „Teilnehmer“) sie tragen — verlangt ist: Verweise werden vom Sync bei
  Platzhaltern und früheren Labels korrekt ersetzt, und derselbe Baum ergibt dieselben Bytes.


## Umfang dieser Task

- Neues Verzeichnis `server/src/viewer/plugins/mindmap/infrastructure/mirror/` nach dem Muster von
  `memos/infrastructure/mirror/`: `syntax.py` (Regexe, Kopfzeilen, Hilfen), `decode.py`, `encode.py`, `codec.py`
  (`MindmapCodec`). Reine Funktionen; der Codec bekommt wie `MemosCodec` den Projektnamen über `for_project`.
- Das Schreiben folgt `MirrorCodec.encode(upserts, removed, current) -> Sequence[Change]` in
  `server/src/viewer/core/application/sync.py` und benutzt `viewer.core.domain.files` (`Change`, `FileSet`) wie
  `memos/…/encode.py`.
- Regeln beim Lesen (Code der Fehler wie im Memos-Spiegel, mit Datei und Zeile): `format_version` (Kennung im
  Baum), `unknown_field`, `missing_field`, `invalid_value`, `duplicate_uid`, `duplicate_label`,
  `file_label_mismatch`, `invalid_placeholder`, `merge_markers`, dazu `duplicate_node_in_tree` und `tree_cycle`.
  `unknown_reference` kann nur die Datenbank entscheiden (Teilnehmer, nächste Task).
- Die Prüfung „ein Item bei höchstens einem Knoten“ gehört nicht in den Codec (er sieht nur Dateien und kann sie
  prüfen: zwei Knotendateien nennen dasselbe Item → `rule_violation` mit beiden Dateien); sie ist hier mit
  umzusetzen, weil sie nur aus den Dateien entscheidbar ist.
- Plugin-Definition (`plugin.py`) bleibt in dieser Task unverändert: der Codec wird erst mit dem Teilnehmer
  registriert.

## Tests

- Unit: `tests/implementation/unit/server/plugins/mindmap/test_mirror_encode.py` und `test_mirror_decode.py`
  (Muster: `…/plugins/backlog/test_mirror_encode.py`, `…/memos/…`).
- Golden-Files: `tests/fixtures/mirror-mindmap/` mit `README.md`, `valid/` (Projektbaum, freie Map, Knoten mit
  Zuordnungen, ein Knoten in zwei Bäumen, entfernte Platzierungen, Papierkorb, Dokumente, Platzhalter-Knoten und
  -Map aus der Cloud) und `invalid/<fehlercode>/` je Fehler; Byte-Gleichheit beim Schreiben (`encode(decode(x)) == x`).
- Das Format-Kapitel in `docs/techdocs/interfaces.md` schreiben, bevor der Code entsteht (es ist der Vertrag der
  folgenden Tasks).

## Nicht Teil

Datenbank, Teilnehmer, Registrierung beim Sync, Oberfläche.
