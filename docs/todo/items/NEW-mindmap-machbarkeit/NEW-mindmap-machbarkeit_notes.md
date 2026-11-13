# NEW-mindmap-machbarkeit — Mindmap: Machbarkeit prüfen und Ideen sammeln

## State

- Goal/Status: Ideensammlung läuft; Grundmodell (eigenes Gerüst aus Themenknoten, Items werden verlinkt) ist mit dem Owner abgestimmt, Details offen.
- Next step: Offene Fragen mit dem Owner klären, dann das Konzept als Spec schreiben.
- Open:
  - Zuordnung: nächste ausdrückliche Zuordnung gewinnt (eigene, sonst die des Parents)? Vorschlag, noch nicht bestätigt (2026-11-13)
  - Projektübergreifende Ansicht: Projekt-Maps nebeneinander über die Projektauswahl statt eigener globaler Map? Vorschlag, noch nicht bestätigt (2026-11-13)
  - „Ein Knoten je Item“ als Regel über der Verknüpfungstabelle statt als Liste mit list[0]? Vorschlag, noch nicht bestätigt (2026-11-13)
  - Wie die KI Knoten vorschlägt: nur im Gespräch oder als sichtbarer Vorschlag in der Oberfläche (2026-11-13)
  - Abgeschlossene Items: nur im Fortschritt zählen oder auch zeigen (2026-11-13)
  - Überführen eines Ideen-Knotens ins Backlog: Typwahl, Umgang mit Knoten tiefer als drei Ebenen (2026-11-13)
  - Verhältnis zu Memos und Topics: Idee auch zu einem Memo machen? (2026-11-13)
- Decided:
  - Die Mindmap ist ein eigenes Datenmodell und nur ein Gerüst; Backlog-Items werden hineinverlinkt, ähnlich dem Feld Area (2026-11-13)
  - Items sind keine eigenen Knoten; ein Knoten zeigt Anzahl und Fortschritt, die Items stehen im Detail (2026-11-13)
  - Ob ein Knoten nur Idee oder schon im Backlog ist, ergibt sich aus den verlinkten Items; keine zwei Arten von Mindmap (2026-11-13)
  - Knoten können Notizen bekommen (2026-11-13)
  - Abhängigkeiten zwischen Themen sind an- und abschaltbar (2026-11-13)
  - Die KI ordnet neue Items zu und schlägt Knoten vor; neue Knoten legt sie erst nach Bestätigung an (2026-11-13)
  - Ein Item hängt zunächst an genau einem Knoten; mehrere bleiben später möglich (2026-11-13)
  - Vererbung „alles unter einem Epic gehört zum Knoten des Epics“ ohne Ausnahme ist verworfen (2026-11-13)
- References: Graph-Seite `client/src/plugins/backlog/` (`graphModel.ts`, React Flow, ELK); `workspace_links`, `ElementDetail`, `DocumentsSection`; Story STORY-086 (Umwandeln)

State confirmed after entry 2026-11-13 — Idee, Grundmodell und erste Entscheidungen (6427b6a7d072)

## 2026-11-13 — Idee, Grundmodell und erste Entscheidungen

### Discussed

- Ausgangsidee des Owners: den Backlog auch als Mindmap zeigen und unabhängig davon eine Brainstorming-Mindmap, aus der ganz oder teilweise ins Backlog überführt wird.
- Erste Einschätzung: Eine Mindmap der Hierarchie Epic → Story → Task bringt wenig, weil sie nur den Baum wiederholt. Der Owner stellt klar: gemeint ist keine Drei-Ebenen-Ansicht, sondern ein thematisches Clustern, gemischt aus Backlog und Abhängigkeiten, in dem nicht jedes Detail steht.
- Clustern ohne KI: geht aus Abhängigkeitsgruppen (`connectedComponents`), dem Feld Area und dem gemeinsamen Epic. Es endet beim Benennen der Themen, bei Items ohne Abhängigkeit und bei Themen, die quer zu den Epics liegen. Textähnlichkeit über Titel ist bei kurzen Titeln schwach.
- Berechnete oder gespeicherte Themen: Bei jeder Berechnung springen Layout und Namen. Empfehlung: Themen sind gespeicherte Knoten, an denen Items hängen; wer zuordnet (Owner per Ziehen, KI über die API), ist dann offen. Der Viewer braucht keine eigene LLM-Anbindung.
- Übersichtlichkeit (Kernanforderung des Owners: mit wenigen Schritten sehen, was es gibt und was kommt; die Menge der Tasks darf die Map nicht füllen). Vorschläge: Items nie als Knoten, nur Zahl und Fortschrittsring; Zustand des Knotens abgeleitet (Idee, geplant, in Arbeit, erledigt) mit Filter; Abhängigkeiten nur zwischen Themen zusammengefasst; standardmäßig zwei Ebenen offen; die KI hängt an bestehende Themen, Unpassendes in einen Sammelknoten „Nicht zugeordnet“.
- Zuordnung nur am Wurzel-Item mit Vererbung an alle Kinder: Der Owner widerspricht. Beispiel: Epic „UI neu schreiben“ hängt am Knoten „Neubau UI“; darunter plant er die Knoten Builder, Patients, ProcessManager. Stories des Epics müssen an diese Unterknoten gehängt werden können. Neuer Vorschlag: Vererbung ist nur der Standard, die nächste ausdrückliche Zuordnung gewinnt (die eigene, sonst die des Parents); jedes Item zählt einmal an seinem wirksamen Knoten, übergeordnete Knoten zeigen die Summe.
- Epics werden oft selbst Knoten sein, darunter wird eher gruppiert; dafür braucht es keine Sonderregel.
- Projekt und projektübergreifend: Der Owner möchte die Map je Projekt und über alle Projekte, fragt aber, ob das die Oberfläche überfrachtet. Vorschlag: eine Map je Projekt mit dem Projekt als Wurzel; die Projektauswahl der Seitenleiste zeigt mehrere Projekt-Maps nebeneinander, wie im Baum. Keine zweite Ansicht; echte projektübergreifende Themenknoten erst bei Bedarf.
- Ein oder mehrere Knoten je Item: Der Owner schlägt eine Liste vor, von der zunächst list[0] gilt. Gegenvorschlag: Verknüpfungen liegen ohnehin in einer n:m-Tabelle (`workspace_links` mit Rollen); „höchstens ein Thema je Item“ ist dann eine Regel der Domain, die sich später ohne Migration lockern lässt. Eine Liste mit list[0] macht unklar, was die weiteren Einträge bedeuten, und führt zu doppeltem Zählen.
- Machbarkeit, erster Blick: React Flow und ELK sind für den Abhängigkeiten-Graphen vorhanden. Als Element des Workspace bekäme ein Knoten Verknüpfungen, Papierkorb und über `DocumentsSection` Notizen aus vorhandenen Bausteinen.

### Decided

- Eigenes Datenmodell als Gerüst, Items werden verlinkt; die Map dient dem Brainstormen und zugleich als Übersicht des Backlogs (Owner).
- Items sind keine Knoten; der Zustand eines Knotens ergibt sich aus den verlinkten Items, es gibt keine zwei Arten von Mindmap.
- Knoten können Notizen bekommen, um Allgemeines zum Thema festzuhalten (Owner).
- Abhängigkeiten zwischen Themen nur an- und abschaltbar, sonst wird es unübersichtlich (Owner).
- Die KI überlegt beim Anlegen von Items, wohin sie gehören, und darf Knoten und Unterknoten vorschlagen; angelegt werden sie erst nach Bestätigung (Owner).
- Zunächst genau ein Knoten je Item, erweiterbar gehalten (Owner).
- Verworfen: strikte Vererbung vom Wurzel-Item ohne Ausnahme, weil sie das Planen unterhalb eines Epic-Knotens verhindert (Owner).
- Verworfen: Clustern über Textähnlichkeit als Grundlage, zu schwach bei kurzen Titeln.

### Open

- Zuordnung mit „nächste ausdrückliche Zuordnung gewinnt“: Vorschlag, wartet auf den Owner.
- Projektübergreifende Ansicht über die Projektauswahl statt eigener globaler Map: Vorschlag, wartet auf den Owner.
- Verknüpfungstabelle mit Regel statt Liste mit list[0]: Vorschlag, wartet auf den Owner.
- Form der KI-Vorschläge: nur im Gespräch oder als sichtbarer Vorschlag in der Oberfläche.
- Abgeschlossene Items: nur im Fortschritt zählen oder auch zeigen.
- Überführen eines Ideen-Knotens ins Backlog: Typwahl und Knoten tiefer als drei Ebenen.
- Verhältnis zu Memos und Topics.
