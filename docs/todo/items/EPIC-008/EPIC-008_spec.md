# EPIC-008 — Konzept: Mindmap als Themen-Gerippe

Stand der Planung. Der Weg zu den Entscheidungen steht in den Notizen des Tasks
`TASK-064`; die Einzelheiten je Fähigkeit stehen in den Notizen der Stories.

## Zweck

- Brainstormen: Themen sammeln, ordnen und verfeinern, unabhängig vom Backlog.
- Übersicht: mit wenigen Schritten sehen, was es gibt und was kommt. Die Menge der Stories und Tasks
  darf die Darstellung nicht füllen.
- Die Mindmap ist nur ein Gerippe. Sie verlinkt Backlog-Items und Memos und kopiert nichts.

## Begriffe

- **Knoten:** ein Thema mit Titel und optionalem Text; kann Notizen tragen, darf leer sein, beliebige Tiefe.
- **Baum (Map):** Knoten unter einer Wurzel. Es gibt den **Projektbaum** (einer je Projekt, das Projekt ist die
  Wurzel), **freie Maps** (beliebig viele je Projekt, Übergreifendes im Projekt „Allgemein“). Eine eigene Map je Memo gibt es
  nicht; ein Memo wird an einen Knoten verlinkt, auch in freien Maps (die Map selbst ist kein Ziel).
- **Platzierung:** die Lage eines Knotens in einem Baum (Knoten, Parent, Stelle). Ein Knoten kann Platzierungen
  in mehreren Bäumen haben, in einem Baum höchstens eine. Platzierungen sind gleichberechtigt.
- **Zuordnung:** die Verknüpfung eines Items oder Memos mit einem Knoten.
- **Wirksamer Knoten** eines Items: der eigens zugeordnete, sonst der wirksame Knoten seines Parents.

## Datenmodell

- Eigenes Plugin `mindmap` auf Server und Client, eigenes Datenmodell.
- Tabellen für Bäume, Knoten und Platzierungen. Platzierungen statt eines Parent-Felds gelten von Anfang an.
- Ein Knoten ist ein Element des Workspace und bekommt so Verknüpfungen und Papierkorb.
- Zuordnungen sind Verknüpfungen (`workspace_links`, eigene Rolle). Die Regel „ein Item hängt an höchstens einem
  Knoten“ liegt in der Domain und lässt sich später lockern, ohne die Daten umzubauen.
- Regeln der Domain: keine Kreise; ein Knoten höchstens einmal je Baum; ein Baum gehört zu einem Projekt.
- Topics der Memos bleiben unverändert und gehören nicht zur Mindmap.

## Zuordnung und Zahlen

- Items sind nie eigene Knoten. Ein Knoten zeigt Anzahl und Fortschrittsring; die Items stehen im Detail.
- Alles erbt vom Parent, außer ein Item ist eigens angehängt; dann zählen es und seine Kinder zum neuen Knoten.
- Ein Epic ist in der Regel ein Knoten, aber nicht zwingend; ein Knoten kann mehrere Epics tragen.
- Summen laufen über Unterknoten und leere Knoten nach oben. Jedes Item zählt genau einmal. Bei übertragenen Ästen
  werden Zahl, Fortschritt und Zustand je Baum aus der dort sichtbaren Struktur berechnet und können je Baum abweichen.
- Zustand eines Knotens, abgeleitet: Idee (keine Items), geplant, in Arbeit, erledigt. Ein Filter darüber. Regel und Zählung: `STORY-100_spec.md`.
- Memos lassen sich verlinken und stehen nur im Detail.
- Items ohne Knoten stehen in der Seitenansicht „Nicht zugeordnet“ (kein Knoten, ausschaltbar, Drag-and-drop in den
  Baum). Einzelheiten: `STORY-100_spec.md`.

## Darstellung

- Eigene Seite. Beim Öffnen sind zwei Ebenen offen.
- **Auswahl der Maps:** Liste in der Seitenleiste (Projektbaum zuerst, dann freie Maps); dort auch Anlegen,
  Umbenennen, Löschen. Die Gesamtansicht zeigt nur Projektbäume, keine freien Maps.
- **Fokus (Anker):** jeder Knoten lässt sich als Wurzel öffnen, mit Pfad zurück. Es ist eine Ansicht, kein
  zweiter Baum.
- **Einzelansicht:** eine Map. **Gesamtansicht:** eine gemeinsame Wurzel, die gewählten Projekte als erste Knoten.
- **Anordnung:** umschaltbar zwischen rund und Baum zur Seite.
- **Abhängigkeiten:** nur zwischen Themen zusammengefasst, an- und abschaltbar, standardmäßig aus.
- **Am Item:** „Gehe hin“ (Map an seiner Stelle), „Erstelle“ (eigener Knoten), „Anker“ (als Wurzel öffnen, erst
  nach „Erstelle“).
- Aufbau zunächst wie im Backlog: Sidebar, Baum zur Seite, Detailspalte; die Detailspalte ist schließbar. Auswahl der Maps und Schalter kommen mit den späteren Stories; der Aufbau darf dann angepasst werden.
- Die Mindmap ersetzt das Feld Area: Area entfällt ganz, das Thema eines Items kommt aus seinem Knoten; den ersten Baum erzeugt eine KI mit einem Prompt (`STORY-106`).

## Äste zwischen Bäumen

- **Umhängen:** aus A weg, in B drin; innerhalb eines Baums und zwischen Bäumen, nur innerhalb eines Projekts.
- **Bedienung:** Kontextmenü „Umhängen nach …“ / „Übertragen nach …“ und Ziehen auf einen Eintrag der Map-Liste mit Wahl; der Ast landet unter der Wurzel der Ziel-Map. Beides gibt es auch über API und MCP, damit die KI Äste verschieben kann.
- **Übertragen:** derselbe Ast in A und B; nur zwischen Bäumen. Der Ast ist ein gemeinsamer Datensatz: Inhalt (Titel, Text, Notizen, Items)
  ist überall gleich; die Struktur darunter gehört je Baum. Ein neuer Unterknoten erscheint in allen Bäumen, in
  denen sein Parent steht; Umhängen und „Hier entfernen“ darunter gelten nur im bearbeiteten Baum. Übertragene Äste sind markiert: ein Symbol mit der Zahl der Bäume erscheint beim Überfahren und bietet die Bäume des Knotens zum Springen an; ein Schalter in den Filtern färbt alle übertragenen Äste mit einem Rand ein. „Gehe hin“ zu einem Knoten in mehreren Bäumen fragt per Auswahl nach dem Baum.
- „Hier entfernen“ nimmt den Ast aus einem Baum, „Knoten löschen“ überall. Steht ein Knoten nur in einem Baum, gibt es nur „Löschen“; „Knoten löschen“ eines geteilten Knotens fragt vorher mit den betroffenen Bäumen. Verliert ein Knoten seine letzte Platzierung, kommt er mit den heimatlos gewordenen Unterknoten in den Papierkorb, nie ins Leere. Beides gibt es getrennt über API und MCP.
- Ein „Trennen“ in eine eigenständige Kopie gibt es vorerst nicht; bei Bedarf wird umgebaut.

## Ins Backlog und Rolle der KI

- Aus einem Ideen-Knoten wird ein Item oder ein Memo angelegt; der Knoten bleibt stehen und das Ergebnis hängt daran. Typ und Beziehung (Parent-Child oder Abhängigkeit) legt je Knoten ein Mensch oder die KI fest, es gibt keine Ableitung aus Ebene oder Tiefe. Ein Memo ändert den Zustand des Knotens nicht (`STORY-100_spec.md`).
- Ganze Äste lassen sich mit Vorschau überführen. Es gibt keinen Automatismus: Typ (Epic, Story, Task) oder Memo und die
  Beziehung (Parent-Child, Abhängigkeit oder keine) legt ein Mensch oder die KI für jeden Knoten einzeln fest, auch
  für Knoten tiefer als drei Ebenen (ein Knoten in Tiefe 5 kann ein eigenes Epic sein). Die Vorschau zeigt nur, was die
  Struktur des Backlogs nicht erlaubt; die Regeln des Backlogs liefert das Plugin backlog.
- Die KI ordnet beim Anlegen eines Items zu, schlägt Knoten vor und legt sie nach Bestätigung an. Sie arbeitet
  über API und MCP; der Viewer hat keine eigene LLM-Anbindung. Ein Vorschlag erscheint im Gespräch, nicht als
  gespeicherter Zustand; ohne Zustimmung entsteht kein Knoten und das Item steht unter „Nicht zugeordnet“. Die Regel
  steht in den MCP-Tool-Beschreibungen des Viewers und wird als Skill-Regel an Claude_Harness übergeben, durch einen
  Prompt, den der Owner selbst weitergibt.
- Markdown-Spiegel: mitgeplant, nicht Pflicht; nötig, damit Cloud-Sitzungen zuordnen können. Er muss auch freie
  Maps enthalten, damit eine Cloud-Sitzung sie beim Brainstormen füllen kann. Format: der Inhalt eines Knotens steht
  einmal in einer Datei, jeder Baum ist eine eigene Datei mit Verweisen auf Knoten, mehrfache Platzierungen sind
  Verweise; die Zuordnung von Items und Memos steht auf dem Knoten, nicht im Item. Das Format hat eine eigene
  Versionszählung (Details in `NEW-mirror-format_spec.md`).
- Area entfällt ganz (`STORY-106`): kein abgeleiteter Wert, die Schichten Web-UI und Backend-API sind keine
  Einordnung mehr; das Thema eines Items steht im Abschnitt „Knoten“ der Mindmap. Das Backlog-Dateiformat wird
  Version 3 ohne Area (Version 2 und 3 werden gelesen, Area wird ignoriert). Den ersten Themenbaum erzeugt eine KI aus
  den vorhandenen Items; der Owner bekommt dafür einen fertigen Prompt.
- Idee, nicht geplant: Export einer freien Map als verschachtelte Liste in ein Memo (einmalig, später bei Bedarf).

## Vorhandene Bausteine

- Darstellung: React Flow und ELK wie der Abhängigkeiten-Graph (`client/src/plugins/backlog/`, `graphModel.ts`,
  `graphLayout.ts`); ELK bietet `radial`, `mrtree` und `layered`.
- Verknüpfungen: `workspace_links` mit Rollen; Detail fremder Elemente über `ElementDetail`.
- Notizen: `DocumentsSection`. Papierkorb: Workspace. Kreisprüfung: Vorbild Topics (`topic_loop`).

## Rahmen der Umsetzung

- Eigener neuer Branch, weil großer experimenteller Umbau; viele kleine Schritte.
- Reihenfolge: Gerüst, dann Zuordnung, dann Ansichten und freie Maps, danach Area entfernen (`STORY-106`), Überführen (`STORY-103`), KI (`STORY-104`) und zuletzt der Spiegel (`STORY-105`).

## Offen

- Runde Anordnung bei großen Maps (Prototyp).
- Alles Übrige ist entschieden und in den Specs der Tasks zu `STORY-103` bis `STORY-106` festgehalten.
