# TASK-072 — Prompt 2: Claude_Harness auf Format Version 3 ohne Area anpassen

Der Text zwischen den Linien ist ein einziger Prompt. Der Owner kopiert ihn in eine Sitzung im Repository von
Claude_Harness. Die Stellen stammen aus der kopierten Fassung des Harness in diesem Repository (`.claude/skills/`,
`.claude-harness/runtime/`); sie sind der Hinweis, wo zu suchen ist, nicht die vollständige Liste. Die Änderungen am
Mindmap-Spiegel (Format `mindmap.md`) sind nicht Teil dieses Prompts, sondern von `TASK-082`.

---

Passe Claude_Harness an eine Änderung des ToDo-Viewers an: Das Feld **`Area`** der Backlog-Items entfällt ganz, und
das Backlog-Dateiformat heißt jetzt **Version 3**. Die Einordnung nach Themen übernehmen die Knoten der Mindmap im
Viewer; die Harness-Skripte und -Skills kennen sie nicht und sollen sie nicht nachbauen. Arbeite nur in diesem
Repository (Claude_Harness); ändere nichts in einem Projekt, das den Harness nutzt, und übergib nichts an andere
Repositories. Lies zuerst die Skills `todo` und `techdocs` dieses Repositories, suche dann mit `grep -rniw area` über
das ganze Repository (Skills, Skripte, Vorlagen, Tests, README, Doku, die kopierte Fassung für Cloud-Sitzungen,
Beispiele in Skill-Texten und Hooks) und arbeite die Liste unten ab. Die Liste nennt Fundorte als Anhalt; jeder
Treffer des Suchworts, der das Backlog-Feld meint, wird angepasst.

## 1. Backlog-Dateiformat Version 3 (Dateimodus)

Version 3 ist Version 2 ohne das Feld `Area`. Lesen: Version 2 **und** 3. Schreiben: nur 3.

- Kennung: „backlog format version 3“ (statt 2) in der Formatzeile von `TODO.md` und `archive.md`, in den Vorlagen
  (`templates/todo/TODO.md`, `archive.md`), in `format.md` (Überschrift „Claude_Harness backlog format, version 3“ und
  der Abschnitt „Version 2 is the only valid format …“: Version 2 und 3 werden gelesen, Version 1 und fehlende
  Kennung sind veraltet).
- Das Feld `Area` entfällt aus der Feldliste und dem Beispiel (`format.md`: Beispieleintrag, Feldreihenfolge
  „`Uid`, `Type`, `Parent`, `Required for parent`, `Status`, `Created`, `Priority`, `Dependencies`, `Goal`,
  `Completion criteria`, `Summary`, `Resolution`, `Deleted`“), aus den Pflichtfeldern („Every entry contains …“) und
  aus dem Absatz „Areas are free text …“ (entfällt ganz).
- **Toleranz:** Ein Eintrag mit `Area` (Version 2, oder ein altes Feld in einer Version-3-Datei) ist kein Fehler: das
  Feld wird gelesen und ignoriert; es meldet weder `unknown field` noch „missing field“. Geschrieben wird es nie.
  Ein Eintrag, den das Skript ohnehin ändert, verliert das Feld; ein unveränderter wird nicht allein deswegen
  umgeschrieben.
- Skripte: `scripts/backlog.py` (Feldliste `FIELDS`/Pflichtfelder, Datenklasse mit `area`, Parser, `--index`),
  `scripts/check_backlog.py` und was sonst die Feldliste prüft; die Formatkennung wird an allen Stellen geprüft, die
  heute „version 2“ verlangen. Der Backlog-Check, die Hooks und `session_start.py` müssen eine Version-2- und eine
  Version-3-Datei beide ohne Meldung annehmen.
- Tests der Skripte: Fälle für Version 2 mit Area (wird gelesen, ignoriert), Version 3 ohne Area, Version 3 mit
  Area (ignoriert, kein Fehler), eine Datei mit anderer Version (Fehler).
- Alarme (`alarms.md`) und Memos bleiben unverändert.

## 2. Index und Übersichten

- Die Index-Zeile heißt `ID | Type | Status | Title | Parent` (ohne Spalte Area) im Dateimodus (`backlog.py --index`,
  `format.md`, Abschnitt „Overview index“) und im API-Modus (`backlog_api.py index`, `api.md`). Der Viewer liefert
  zusätzlich die Spalte `Notes` (Zustand des Kopfs der Notizen oder `-`): `ID | Type | Status | Title | Parent | Notes`;
  prüfe, ob der Helfer sie übernimmt und `api.md` sie nennt.
- `SKILL.md` des `todo`-Skills: die Regel „Reuse existing areas before inventing new ones“ entfällt; die Aussagen zur
  Ablage neuer Items („Place new work under an existing epic or story …“) bleiben.

## 3. API und MCP des Viewers

Der Viewer (Stand nach der Entfernung) kennt `area` nirgends mehr; ein Aufruf mit `area` in `fields` scheitert mit
dem Fehlercode `not_editable` („Das Feld 'area' lässt sich beim Anlegen nicht setzen“), ein Lesen liefert kein Feld.

- `backlog_api.py`: der Befehl `areas` (GET `/backlog/areas`) entfällt, samt Hilfetext, `ARITY`, Tests und `api.md`.
- `create`: `area` entfällt aus den Eingabefeldern (`backlog_api.py`-Hilfe, `api.md`, Beispiele). Die Pflichtfelder
  sind `type`, `title`, `goal`, `completion_criteria`.
- `update`: `area` entfällt aus der Liste der änderbaren Felder.
- `memos_api.py promote`: `fields` ohne `area` (nötig sind `goal`, `completion_criteria`; `memos_api.py`-Hilfe,
  `memos-api.md`, Abschnitt „Memo to backlog item“ in `memos.md`: „propose parent, area, goal …“ wird „parent, goal …“).
- Antworten von `show`/`list` enthalten kein `area`; Skripte und Skill-Texte, die es auslesen, entfallen.
- Wenn der Harness die MCP-Tools des Viewers nutzt: `backlog_list_areas` gibt es nicht mehr; `backlog_create_item`,
  `backlog_update_item` und `memos_promote_memo` nehmen kein `area`; `backlog_index_lines` liefert die Kopfzeile
  oben.
- Neu im Viewer, für den Harness **nicht** nachzubauen, aber in `SKILL.md`/`api.md` in einem Satz zu nennen: Das
  Thema eines Items ist der Knoten der Mindmap, an dem es hängt (Tools `mindmap_…`, z. B. `mindmap_get_item_node`,
  `mindmap_assign_item`; oder der Abschnitt „Knoten“ im Detail des Items). Es gibt dafür keinen Filter und keine
  Spalte in den Index-Zeilen.

## 4. Vorschläge und Texte

- „Proposing new items“ in `format.md` und die entsprechenden Stellen in `SKILL.md`: „A proposal states title, type,
  goal, completion criteria, area, and priority“ → ohne area.
- Alle Beispiele (Skill-Texte, Befehlsbeispiele, Vorlagen, Tests, README), die ein Item mit `Area:` oder `"area"`
  zeigen, ohne Area.
- `README` und die Changelog-/Versionsangaben des Harness: Format Version 3 und die entfallene Spalte nennen; die
  Versionsnummer des Harness nach seiner eigenen Regel erhöhen (eine inkompatible Änderung der Schnittstelle).

## 5. Verteilung

- Die kopierte Fassung für Cloud-Sitzungen (`[cloud] export = true`, erzeugt von `/claude-harness:init` und
  `/claude-harness:update`) entsteht aus den Änderungen oben; ändere sie nicht von Hand, sondern erzeuge sie neu und
  nenne dem Owner, dass die Projekte `update` ausführen müssen.
- Projekte mit einer Version-2-Datei brauchen keine Umstellung: Sie werden weiter gelesen; beim ersten Schreiben
  entsteht Version 3. Bei Projekten mit dem Viewer geschieht das durch den Spiegel des Viewers.

## 6. Prüfen

- Alle Tests des Harness laufen grün (Befehl laut dessen Test-Doku; bei einer fehlenden Umgebung richte sie ein).
- `grep -rniw area` findet danach nur noch: die Erklärung der Toleranz in `format.md`, die Tests dafür und
  Verwendungen des Wortes in anderem Sinn (z. B. „text area“); nenne die Resttreffer im Bericht.
- Probiere an einer synthetischen Version-2-Datei mit `Area`: Check, `--index` und `--show` laufen ohne Fehler; eine
  Änderung mit dem Skript im Dateimodus schreibt Version 3 ohne Area.
- Bericht: geänderte Dateien, Teststand, Resttreffer von „area“, offene Fragen.

---
