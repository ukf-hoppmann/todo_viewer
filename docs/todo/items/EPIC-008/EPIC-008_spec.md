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
  Wurzel), **freie Maps** (beliebig viele je Projekt, Übergreifendes im Projekt „Allgemein“) und die **Map eines
  Memos** (lebt allein in diesem Memo).
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
- Summen laufen über Unterknoten und leere Knoten nach oben. Jedes Item zählt genau einmal, auch wenn sein Ast
  über zwei Wege unter derselben Wurzel liegt.
- Zustand eines Knotens, abgeleitet: Idee (keine Items), geplant, in Arbeit, erledigt. Ein Filter darüber.
- Memos lassen sich verlinken und stehen nur im Detail.
- Items ohne Knoten stehen im Sammelknoten „Nicht zugeordnet“.

## Darstellung

- Eigene Seite. Beim Öffnen sind zwei Ebenen offen.
- **Fokus (Anker):** jeder Knoten lässt sich als Wurzel öffnen, mit Pfad zurück. Es ist eine Ansicht, kein
  zweiter Baum.
- **Einzelansicht:** eine Map. **Gesamtansicht:** eine gemeinsame Wurzel, die gewählten Projekte als erste Knoten.
- **Anordnung:** umschaltbar zwischen rund und Baum zur Seite.
- **Abhängigkeiten:** nur zwischen Themen zusammengefasst, an- und abschaltbar, standardmäßig aus.
- **Am Item:** „Gehe hin“ (Map an seiner Stelle), „Erstelle“ (eigener Knoten), „Anker“ (als Wurzel öffnen, erst
  nach „Erstelle“).
- Aufbau zunächst wie im Backlog: Sidebar, Baum zur Seite, Detailspalte; die Detailspalte ist schließbar. Auswahl der Maps und Schalter kommen mit den späteren Stories; der Aufbau darf dann angepasst werden.
- Die Mindmap ersetzt das Feld Area; wie, regelt eine eigene Story.

## Äste zwischen Bäumen

- **Umhängen:** aus A weg, in B drin; innerhalb eines Baums und zwischen Bäumen.
- **Übertragen:** derselbe Ast in A und B; nur zwischen Bäumen. Der Ast ist ein gemeinsamer Datensatz, eine
  Änderung wirkt an beiden Stellen. Übertragene Äste sind markiert.
- „Hier entfernen“ nimmt den Ast aus einem Baum, „Knoten löschen“ überall.
- Ein „Trennen“ in eine eigenständige Kopie gibt es vorerst nicht; bei Bedarf wird umgebaut.

## Ins Backlog und Rolle der KI

- Aus einem Ideen-Knoten wird ein Item angelegt; der Knoten bleibt stehen und das Item hängt daran.
- Die KI ordnet beim Anlegen eines Items zu, schlägt Knoten vor und legt sie nach Bestätigung an. Sie arbeitet
  über API und MCP; der Viewer hat keine eigene LLM-Anbindung.
- Markdown-Spiegel: mitgeplant, nicht Pflicht; nötig, damit Cloud-Sitzungen zuordnen können.

## Vorhandene Bausteine

- Darstellung: React Flow und ELK wie der Abhängigkeiten-Graph (`client/src/plugins/backlog/`, `graphModel.ts`,
  `graphLayout.ts`); ELK bietet `radial`, `mrtree` und `layered`.
- Verknüpfungen: `workspace_links` mit Rollen; Detail fremder Elemente über `ElementDetail`.
- Notizen: `DocumentsSection`. Papierkorb: Workspace. Kreisprüfung: Vorbild Topics (`topic_loop`).

## Rahmen der Umsetzung

- Eigener neuer Branch, weil großer experimenteller Umbau; viele kleine Schritte.
- Reihenfolge: Gerüst, dann Zuordnung, dann Ansichten und freie Maps, danach Überführen, KI und Spiegel.

## Offen

- Runde Anordnung bei großen Maps (Prototyp).
- Form der KI-Vorschläge; abgeschlossene Items zeigen; Typwahl und tiefe Knoten beim Überführen; Markierung für Ideen-Knoten; Dateiformat für Platzierungen.
