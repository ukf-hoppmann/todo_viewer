# NEW-mindmap-machbarkeit — Mindmap: Machbarkeit prüfen und Ideen sammeln

## State

- Goal/Status: Ideensammlung läuft; Grundmodell, Zuordnung und Ansichten sind mit dem Owner abgestimmt, das allgemeine Modell (Map an beliebigem Element) ist vorgeschlagen.
- Next step: Offene Fragen mit dem Owner klären, dann das Konzept als Spec schreiben.
- Open:
  - Map mit Anker (Projekt oder Element) als ein gemeinsames Modell, Projekt-Map zuerst, Element-Maps als zweiter Schritt? Vorschlag, noch nicht bestätigt (2026-11-13)
  - Folge daraus: „höchstens ein Knoten je Item“ gilt je Map, nicht insgesamt? Vorschlag, noch nicht bestätigt (2026-11-13)
  - Wie die KI Knoten vorschlägt: nur im Gespräch oder als sichtbarer Vorschlag in der Oberfläche (2026-11-13)
  - Abgeschlossene Items: nur im Fortschritt zählen oder auch zeigen (2026-11-13)
  - Überführen eines Ideen-Knotens ins Backlog: Typwahl, Umgang mit Knoten tiefer als drei Ebenen (2026-11-13)
  - Verhältnis zu Memos und Topics: Idee auch zu einem Memo machen? (2026-11-13)
  - Runde Anordnung bei großen Maps: ELK `radial` oder eigene Anordnung, im Prototyp prüfen (2026-11-13)
- Decided:
  - Die Mindmap ist ein eigenes Datenmodell und nur ein Gerippe; sie verlinkt Backlog-Items, ähnlich dem Feld Area (2026-11-13)
  - Ein Epic ist in der Regel ein Knoten, aber nicht zwingend; ein Knoten kann mehrere Epics tragen (2026-11-13)
  - Items sind keine eigenen Knoten; ein Knoten zeigt Anzahl und Fortschritt, die Items stehen im Detail (2026-11-13)
  - Ob ein Knoten nur Idee oder schon im Backlog ist, ergibt sich aus den verlinkten Items; keine zwei Arten von Mindmap (2026-11-13)
  - Zuordnung: alles erbt vom Parent, außer ein Item ist eigens angehängt; dann zählen es und seine Kinder zum neuen Knoten (2026-11-13)
  - Ein Item hängt zunächst an genau einem Knoten; gespeichert als Verknüpfung mit Regel, nicht als Liste (2026-11-13)
  - Knoten können Notizen bekommen (2026-11-13)
  - Abhängigkeiten zwischen Themen sind an- und abschaltbar (2026-11-13)
  - Die KI ordnet neue Items zu und schlägt Knoten vor; neue Knoten legt sie erst nach Bestätigung an (2026-11-13)
  - Zwei Ansichten: Einzelansicht (eine Map) und Gesamtansicht mit gemeinsamer Wurzel, Projekte als erste Knoten, gefiltert über die Projektauswahl (2026-11-13)
  - Anordnung umschaltbar zwischen rund und Baum zur Seite (2026-11-13)
- References: Graph-Seite `client/src/plugins/backlog/` (`graphModel.ts`, React Flow, ELK); `workspace_links`, `ElementDetail`, `DocumentsSection`; Story STORY-086 (Umwandeln)

State confirmed after entry 2026-11-13 — Zuordnung bestätigt, Ansichten, Map an beliebigem Element (bd2b27b59a95)

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

## 2026-11-13 — Zuordnung bestätigt, Ansichten, Map an beliebigem Element

### Discussed

- Open vom 2026-11-13 (Zuordnung) geklärt: Der Owner bestätigt „alles erbt, wenn nicht eigens anders angehängt; dann zählen das Element und seine Kinder zum neuen Knoten“.
- Open vom 2026-11-13 (Liste oder Verknüpfungstabelle) geklärt: Der Owner stimmt der Verknüpfung mit Regel zu.
- Epics und Knoten: Der Owner stellt klar, dass ein Epic nicht zwingend ein Knoten ist. Beim Brainstormen denkt man größer, z. B. Knoten „Usermanagement“ mit drei Epics (Tool entscheiden, anbinden, Regeln festlegen). Die Map ist nur Gerippe und verlinkt. Das Modell deckt das ab, weil ein Knoten beliebig viele Items tragen kann.
- Open vom 2026-11-13 (projektübergreifende Ansicht): Der Owner will nicht mehrere Maps nebeneinander, weil das vor allem bei runder Anordnung unübersichtlich wird. Stattdessen Einzelansicht und eine Gesamtansicht mit einer gemeinsamen Wurzel, unter der die Projekte die ersten Knoten sind; Projekte lassen sich wie im Backlog hinzu- und wegschalten.
- Anordnung: Der Owner möchte nicht zwingend links-rechts oder oben-unten, sondern gern rund, am besten umschaltbar (zwei Beispielbilder: Mitte mit Ästen ringsum, und Baum nach rechts). Einschätzung: Beide Anordnungen entstehen aus demselben Baum; ELK bietet `radial`, `mrtree` und `layered`. Offen ist, wie gut `radial` bei großen Maps aussieht.
- Allgemeineres Modell (Idee des Owners): von einer Story, einem Epic, Task oder Memo aus „zur Mindmap“ gehen; das Element ist dann die Wurzel und man baut darauf auf. Beim Memo speist sich die Map nur aus dem einen Memo.
- Einschätzung dazu: sinnvoll und umsetzbar, wenn es ein Modell bleibt. Vorschlag: Eine Map hat einen Anker, entweder ein Projekt oder ein Element; alle Elemente haben im Workspace eine `uid`, an der der Anker hängen kann. Die Gesamtansicht ist dann nur eine Darstellung mit künstlicher Wurzel über den Projekt-Maps. Vorteil für die Übersicht: Feinplanung wandert in die Map des Elements, die Projekt-Map bleibt grob; vom Knoten aus öffnet man die Map eines verlinkten Items.
- Risiken des allgemeinen Modells: mehr Umfang, und derselbe Gedanke kann an zwei Stellen stehen (Unterknoten in der Projekt-Map oder eigene Map der Story). Empfehlung: den Anker von Anfang an im Datenmodell vorsehen, aber zuerst nur die Projekt-Map bauen und Element-Maps als zweiten Schritt.
- Folge für die Regel „ein Knoten je Item“: Ein Task kann in der Projekt-Map an einem Knoten hängen und in der Map seiner Story an einem anderen. Die Regel müsste also je Map gelten.

### Decided

- Zuordnung mit Vererbung und ausdrücklicher Ausnahme wie oben (Owner).
- Verknüpfung mit Regel statt Liste mit list[0] (Owner).
- Ein Epic ist in der Regel ein Knoten, aber nicht zwingend; ein Knoten kann mehrere Epics tragen (Owner).
- Einzelansicht und Gesamtansicht mit gemeinsamer Wurzel statt mehrerer Maps nebeneinander (Owner). Verworfen: Projekt-Maps nebeneinander wie im Baum, weil unübersichtlich.
- Anordnung umschaltbar zwischen rund und Baum zur Seite (Owner).

### Open

- Map mit Anker als gemeinsames Modell und die Reihenfolge (Projekt-Map zuerst): Vorschlag, wartet auf den Owner.
- „Höchstens ein Knoten je Item“ je Map statt insgesamt: Vorschlag, wartet auf den Owner.
- Qualität der runden Anordnung bei großen Maps: im Prototyp prüfen.
