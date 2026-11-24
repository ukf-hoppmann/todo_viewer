# TASK-082 — Prompt für Claude_Harness: Mindmap im Datei-Modus

Zweck: Der Owner gibt diesen Prompt in einer Sitzung im Repository von Claude_Harness ein. Die KI dieses Projekts
übergibt ihn nicht selbst. Der Prompt ist eigenständig geschrieben; das Format steht vollständig in
`docs/techdocs/interfaces.md`, Abschnitt „Mindmap-Dateien (Format Version 1)“ des ToDo-Viewers (Repository
`todo_viewer`). Der Owner gibt diese Datei mit oder fügt den Abschnitt in die Sitzung ein.

---

## Prompt

Aufgabe: Bringe der Datei-Modus-Variante des `todo`-Skills bei, die Mindmap eines Projekts zu nutzen. Cloud-Sitzungen
(`CLAUDE_CODE_REMOTE=true`) arbeiten im Modus `files`, ohne Server. Der ToDo-Viewer spiegelt die Mindmap seit Kurzem
in Markdown-Dateien; eine Cloud-Sitzung soll damit Items einem Knoten zuordnen, freie Maps füllen und Äste umhängen
können. Der nächste Sync des Viewers übernimmt die Änderungen mit denselben Regeln wie die API.

Quelle der Wahrheit für das Format ist `docs/techdocs/interfaces.md` des ToDo-Viewers, Abschnitt „Mindmap-Dateien
(Format Version 1)“, samt „Bearbeiten in den Dateien (Cloud-Sitzung)“. Beispiele: `tests/fixtures/mirror-mindmap/valid/`.
Übernimm die Regeln unten in den Skill; schreibe das Format nicht abweichend neu, sondern verweise auf diese Quelle
oder kopiere den Abschnitt in `format.md`.

### 1. Dateien (Ordner `mindmap/` im Backlog-Ordner des Spiegels, neben `TODO.md`)

| Datei | Inhalt |
|---|---|
| `mindmap/NODE-001.md` | ein Knoten: Kopf (`Uid`, `Title`, `Mark`, `Deleted`), `Items:`, `Memos:`, danach der Freitext |
| `mindmap/NODE-001_notes.md`, `NODE-001_spec.md`, `NODE-001_spec_<thema>.md` | Dokumente des Knotens, Text unverändert |
| `mindmap/project.md` | der Projektbaum (genau einer), nur Verweise auf Knoten in ihrer Ordnung |
| `mindmap/maps/<name>.md` | eine freie Map (Brainstorming), gleiche Form wie der Projektbaum, mit `Name:` |
| `mindmap/new-<kurzname>.md`, `mindmap/maps/new-<kurzname>.md` | neuer Knoten bzw. neue Map (Platzhalter) |

Knotenkopf (Reihenfolge fest): `# NODE-001`, `Uid: …`, `Title: …`, `Mark:` (leer, `later` oder `discarded`),
`Deleted:` (leer = in Gebrauch; sonst Zeitpunkt, also im Papierkorb), dann `Items:` und `Memos:` mit je einer Zeile
`- <LABEL>` (Ziel in anderem Projekt: `- <Projekt>:<LABEL>`); die Abschnitte fehlen, wenn sie leer sind. Nach einer
Leerzeile folgt der Freitext bis zum Dateiende.

Baumdatei: Kopf `# <Name>`, `Format: mindmap format version 1`, `Uid`, `Kind: project|free`, bei freien Maps `Name:` und
`Deleted:`; danach eine **Leerzeile** und die Liste: ein Eintrag je Zeile `- NODE-001`, Kinder zwei Leerzeichen
eingerückt, die Reihenfolge ist die Stelle unter den Geschwistern. `Removed:` am Ende nennt entfernte Platzierungen;
die KI ändert diesen Abschnitt nicht, außer der Owner verlangt es.

### 2. Regeln für die Bearbeitung

1. **Der Inhalt eines Knotens steht genau einmal**, in seiner Knotendatei. Bäume enthalten nur Verweise (Labels oder
   Platzhalter) und die Ordnung; ein Knoten steht in einem Baum höchstens einmal.
2. **Neues** (Knoten oder Map) bekommt einen Platzhalter `new-<kurzname>` (`a-z`, `0-9`, `-`, eindeutig): Datei
   `mindmap/new-<kurzname>.md` beginnt mit `# NEW`, hat **keine** `Uid` und kein Label; in der Baumdatei steht
   `- new-<kurzname>`. Eine neue Map liegt in `mindmap/maps/new-<kurzname>.md` (`# NEW`, `Kind: free`, `Name: …`).
   Der Sync vergibt Uid und Label (`NODE-nnn`) und benennt die Dateien um. Nie ein Label oder eine Uid erfinden.
3. **Ast umhängen** heißt: die Zeilen des Asts (den Knoten samt Einrückung seiner Kinder) in der Baumdatei an die neue
   Stelle **verschieben**. Nie einen Knoten kopieren oder neu anlegen, nie einen Knoten zweimal in denselben Baum
   schreiben, nie einen Knoten unter sich oder einen Nachkommen hängen.
4. **Ast in eine andere Map übertragen**: dieselben Labels mit ihren Kindern **zusätzlich** in die Baumdatei der
   Ziel-Map schreiben; die Knotendateien bleiben unverändert. Nur Knoten desselben Projekts.
5. **Item zuordnen**: das Label des Items unter `Items:` der Knotendatei eintragen (Abschnitt anlegen, falls er fehlt).
   Ein Item steht bei **höchstens einem** Knoten; wechselt es den Knoten, wird es beim alten Knoten entfernt. Ein Memo
   darf bei mehreren stehen. Die Item-Dateien (`TODO.md`, Notes) bleiben unverändert: die Zuordnung steht auf dem
   Knoten, nicht im Item.
6. **Nichts löschen.** Löschen und Papierkorb (`Deleted:`) gehören dem Owner; die KI setzt `Deleted:` nicht und
   entfernt keine Dateien.
7. Andere Felder und Dateien nicht anfassen; `Uid`, Dateinamen mit Label und `Format:` bleiben unverändert.
8. Haben beide Seiten denselben Knoten geändert, entscheidet der Owner im Sync-Dialog; die Sitzung löst das nicht.

### 3. Regel für die KI beim Anlegen von Items (aus `STORY-104` des Viewers, im Datei-Modus)

- Wer ein Item anlegt, überlegt, zu welchem Knoten es passt: `mindmap/project.md` und die Knotendateien lesen
  (Titel, Text) und das Item unter `Items:` des passenden Knotens eintragen.
- Passt kein Knoten, **schlägt** die KI im Gespräch einen neuen Knoten (und seinen Parent) vor. Nur **nach der
  Zustimmung des Owners** legt sie ihn als Platzhalter-Datei an und trägt ihn in `project.md` ein. Ohne Zustimmung
  entsteht kein Knoten; das Item bleibt ohne Zuordnung stehen (der Viewer zeigt es unter „Nicht zugeordnet“). Die KI
  erfindet keine Themen.
- Hat das Projekt keinen `mindmap/`-Ordner, legt die KI ihn nicht an; sie sagt dem Owner, dass die Mindmap noch nicht
  gespiegelt ist.

### 4. Änderungen in Claude_Harness

- `todo`-Skill (Datei-Modus, `SKILL.md` und `format.md`): einen Abschnitt „Mindmap“ ergänzen mit Dateien, Feldern und
  den Regeln aus Abschnitt 2 und 3; im Modus `api` unverändert lassen (dort gelten die MCP-Tools `mindmap_*` des Viewers).
- Das Prüfskript (`backlog.py`) und alle Hooks, die den Backlog-Ordner prüfen: Dateien und Ordner unter `mindmap/` sind
  **bekannt** und werden nicht als unbekannte oder fremde Dateien gemeldet. Der Inhalt der Mindmap-Dateien wird dort
  nicht geprüft (das tut der Sync des Viewers, mit Datei und Zeile in der Fehlermeldung); ein einfacher Hinweis bei
  Verstößen, die das Skript leicht erkennt (`Items:` eines Items bei zwei Knoten, Knoten ohne `# NEW` ohne `Uid`),
  ist optional.
- Vorlagen (`runtime/templates/todo/`): unverändert, außer sie listen den Backlog-Ordner; dann `mindmap/` als optional
  nennen.
- Export für die Cloud (`[cloud] export = true`): der Skill-Export muss den neuen Abschnitt enthalten.
- Test: ein Backlog-Ordner mit `mindmap/` (Beispiel: `tests/fixtures/mirror-mindmap/valid/` des Viewers) besteht die
  Prüfung ohne Meldung.

Arbeite nach den Regeln von Claude_Harness (Backlog-Item, Plan, Tests). Nenne mir am Ende, was du geändert hast.
