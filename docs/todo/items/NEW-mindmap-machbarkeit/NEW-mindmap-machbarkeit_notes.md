# NEW-mindmap-machbarkeit — Mindmap: Machbarkeit prüfen und Ideen sammeln

## State

- Goal/Status: Nur Planung, Umsetzung später in kleinen Schritten; Grundmodell, Zuordnung und Ansichten sind abgestimmt, für Maps an Elementen ist „Fokus statt eigener Map“ vorgeschlagen.
- Next step: Offene Fragen mit dem Owner klären, dann das Konzept als Spec schreiben; daraus entsteht später mindestens ein Epic.
- Open:
  - Übertragen technisch: Platzierungen (Knoten, Parent, Stelle) statt eines Parent-Felds, von Anfang an im Datenmodell? Vorschlag, noch nicht bestätigt (2026-11-13)
  - Ein Knoten höchstens einmal je Baum; Summen zählen jedes Item nur einmal? Vorschlag, noch nicht bestätigt (2026-11-13)
  - Getrennte Aktionen „hier entfernen“ und „Knoten löschen“ für übertragene Äste? Vorschlag, noch nicht bestätigt (2026-11-13)
  - Wie die KI Knoten vorschlägt: nur im Gespräch oder als sichtbarer Vorschlag in der Oberfläche (2026-11-13)
  - Abgeschlossene Items: nur im Fortschritt zählen oder auch zeigen (2026-11-13)
  - Überführen eines Ideen-Knotens ins Backlog: Typwahl, Umgang mit Knoten tiefer als drei Ebenen (2026-11-13)
  - Verhältnis zu Memos und Topics: Topics sind selbst ein Baum; bleiben sie daneben, und lassen sich Memos wie Items an Knoten hängen? (2026-11-13)
  - Markdown-Spiegel: Braucht die Mindmap ein Dateiformat, damit sie über Git mitgeht und die KI in Cloud-Sitzungen zuordnen kann? (2026-11-13)
  - Freie Maps: gehören sie zu einem Projekt oder stehen sie darüber, und wo findet man sie? (2026-11-13)
  - Feld Area: bleibt es neben der Mindmap bestehen? (2026-11-13)
  - Eigene Markierung für Ideen-Knoten (z. B. verworfen, später)? (2026-11-13)
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
  - Vorerst wird nur geplant; aus dem Task entsteht später mindestens ein Epic (2026-11-13)
  - Mischung: ein Baum je Projekt mit Fokus auf beliebigem Knoten, dazu freie Maps (2026-11-13)
  - Am Item drei getrennte Aktionen: „Gehe hin“ (Map an der Stelle öffnen), „Erstelle“ (neuen Knoten anlegen), „Anker“ (Element als Wurzel öffnen); kein stilles Anlegen von Knoten (2026-11-13)
  - Umsetzung in einem eigenen neuen Branch, weil großer experimenteller Umbau (2026-11-13)
  - „Anker“ wird an einem Item erst angeboten, nachdem mit „Erstelle“ ein eigener Knoten angelegt wurde (2026-11-13)
  - Äste werden nie kopiert; es gibt „umhängen“ (aus A weg, in B drin) und „übertragen“ (derselbe Ast in A und B) (2026-11-13)
- References: Graph-Seite `client/src/plugins/backlog/` (`graphModel.ts`, React Flow, ELK); `workspace_links`, `ElementDetail`, `DocumentsSection`; Story STORY-086 (Umwandeln)

State confirmed after entry 2026-11-13 — Anker erst nach Erstellen, Sammlung der offenen Grundsatzfragen (d8faac48b51a)

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

## 2026-11-13 — Doppelte Orte: Fokus statt eigener Map, Vergleich mit anderen Werkzeugen

### Discussed

- Frage des Owners: Lassen sich doppelte Orte vermeiden, wenn ein Anker nur die Map ab einem Knoten zeigt? Beispiel: Wurzel → Umbau UI → Builder → ButtonX und → Processmanager → Forms → FormX → ElementY. Jeder Knoten kann Einträge haben oder leer sein (Forms leer, FormX wieder mit Einträgen). Eingeklappt gilt die Summe, je weiter aufgeklappt, desto feiner. Forms wäre dann der Anker, von dem aus geplant wird. Daneben könnten eigenständige Bäume sinnvoll sein, oder eine Mischung.
- Einschätzung: Ja, der Fokus löst die doppelten Orte für alles, was in die Projektstruktur gehört. Es gibt je Projekt einen Baum; ein Anker ist nur eine Ansicht ab einem Knoten, mit Pfad zurück nach oben. Summen laufen auch über leere Knoten nach oben.
- „Zur Mindmap“ an einem Item wird damit zu: Fokus auf den Knoten des Items. Hängt es dort nicht allein, wird unter seinem wirksamen Knoten ein Unterknoten mit seinem Namen angelegt und das Item eigens dorthin gehängt; nach der Vererbungsregel zählen es und seine Kinder dann dort.
- Folge: Der Vorschlag „höchstens ein Knoten je Item je Map“ aus dem vorigen Eintrag entfällt; die Regel kann wieder insgesamt gelten, was einfacher ist.
- Eigenständige Bäume bleiben nötig für das, was noch keinen Platz in einem Projekt hat: freies Brainstorming, eine Map zu einem Memo, Themen über Projekte hinweg. Empfehlung: Mischung. Ein Baum je Projekt mit Fokus, dazu freie Maps mit eigener Wurzel (wahlweise an ein Memo gehängt). Brücke: ein Ast einer freien Map wird in den Projektbaum verschoben, nicht kopiert, damit nichts doppelt steht.
- Andere Werkzeuge (aus dem Wissen der KI, nicht frisch recherchiert):
  - Gliederungswerkzeuge wie Workflowy und Dynalist: ein einziger Baum, jeder Punkt lässt sich als Wurzel öffnen. Das ist genau der Fokus.
  - Mindmap-Programme wie XMind, MindManager, Freeplane: Fokus auf einen Ast („nur diesen Zweig zeigen“) und zusätzlich verknüpfte Teil-Maps, in die ein großer Ast ausgelagert wird. Dort gibt es also beides.
  - User Story Mapping (StoriesOnBoard, Miro): ein Gerüst aus Aktivitäten, unter dem die Stories hängen. Das ist dem Gerippe mit verlinkten Items am nächsten, aber als Raster, nicht als Baum.
  - Mindmap-Erweiterungen für Jira: jedes Ticket ist ein Knoten. Das ist die volle Darstellung, die hier vermieden werden soll.
  - Ein Werkzeug, das ein freies Themen-Gerippe mit geerbter Zuordnung und Summen am Knoten verbindet, ist der KI nicht bekannt.
- Der Owner hält fest: Es wird vorerst nur geplant, damit sichtbar ist, was es gibt und wohin es gehen soll; umgesetzt wird später in vielen kleinen Schritten, aus dem Task entsteht später mindestens ein Epic.

### Decided

- Vorerst nur Planung; später mindestens ein Epic aus diesem Task (Owner).

### Open

- Open vom 2026-11-13 (Map mit Anker als eigene Map je Element, Regel je Map) ersetzt durch: Mischung aus Projektbaum mit Fokus und freien Maps; wartet auf den Owner.
- „Zur Mindmap“ am Item als Fokus mit bei Bedarf angelegtem Unterknoten; wartet auf den Owner.
- Ast aus freier Map in den Projektbaum verschieben; wartet auf den Owner.

## 2026-11-13 — Aktionen am Item, Mischung bestätigt, eigener Branch

### Discussed

- Open vom 2026-11-13 (Mischung aus Projektbaum und freien Maps) geklärt: Der Owner bestätigt die Mischung, damit man flexibel gestalten kann.
- Open vom 2026-11-13 („Zur Mindmap“ als Fokus mit bei Bedarf angelegtem Unterknoten): Der Owner will das trennen statt einer Aktion, die still einen Knoten anlegt. Drei Aktionen: „Gehe hin“ öffnet die Mindmap an der Stelle des Items; „Erstelle“ legt einen neuen Knoten für das Item an; „Anker“ öffnet das Element als Wurzel.
- Rückfrage des Owners, was „Gerippe als Raster“ beim User Story Mapping heißt: Dort hat die Fläche zwei feste Achsen. Oben steht eine Zeile mit den Schritten des Nutzers in zeitlicher Reihenfolge, unter jedem Schritt stapeln sich die Stories nach Wichtigkeit, waagrechte Linien trennen Lieferstufen. Es gibt nur eine Ebene unter dem Gerüst und die Position trägt Bedeutung. Ein Baum hat beliebige Tiefe und keine Bedeutung der Reihenfolge.
- Umsetzung: Der Owner legt fest, dass der Umbau groß und experimentell ist und deshalb in einem neuen Branch laufen muss.

### Decided

- Mischung aus einem Baum je Projekt mit Fokus und freien Maps (Owner).
- Drei getrennte Aktionen am Item: „Gehe hin“, „Erstelle“, „Anker“ (Owner). Verworfen: eine Aktion „Zur Mindmap“, die bei Bedarf selbst einen Unterknoten anlegt.
- Umsetzung in einem eigenen neuen Branch (Owner).

### Open

- „Anker“ an einem Item, das keinen eigenen Knoten hat: den Knoten zeigen, an dem es (auch geerbt) hängt, oder die Aktion erst nach „Erstelle“ anbieten.
- Ast aus freier Map in den Projektbaum verschieben statt kopieren: weiter offen.

## 2026-11-13 — Äste zwischen Bäumen: umhängen und übertragen

### Discussed

- Open vom 2026-11-13 (verschieben statt kopieren): Der Owner will nichts kopieren, aber verlinken. Wird ein Ast immer nur verschoben, schrumpft der Planungsbaum in dem Maß, wie der Umsetzungsbaum wächst. Deshalb beides: umhängen (aus A weg, in B drin) und übertragen (in A und B). Frage: Geht das Verlinken eines Astes in einen anderen Baum auf Datenbankebene?
- Einschätzung: Ja. Der Knoten bleibt ein einziger Datensatz und bekommt mehrere Platzierungen (Knoten, Parent, Stelle) statt eines Parent-Felds. Der Ast steht dann in beiden Bäumen und ist überall derselbe: eine Änderung, eine Notiz oder ein neuer Unterknoten erscheint an beiden Stellen. Workflowy kennt das als gespiegelte Punkte.
- Folgen: Kreise müssen verhindert werden (wie schon bei Topics); die Regel „ein Knoten je Item“ bleibt gültig, weil das Item an einem Knoten hängt und nur der Knoten mehrfach erscheint; in der Gesamtansicht kann ein Item über zwei Wege unter derselben Wurzel liegen, daher müssen Summen jedes Item nur einmal zählen; „entfernen“ braucht zwei Aktionen (nur hier herausnehmen oder den Knoten löschen); im Fokus folgt der Pfad nach oben dem Weg, über den man gekommen ist; übertragene Äste sollten sichtbar markiert sein; das Markdown-Format des Spiegels wird etwas aufwendiger.
- Erwogen und nicht empfohlen: ein Verweis-Knoten, der nur auf den Ast in seinem Ursprungsbaum zeigt. Der Baum bliebe einfacher, aber es gäbe ein Original und einen Verweis; wird das Original entfernt, hängt der Verweis in der Luft. Die Platzierungen sind gleichberechtigt und passen zu „in A und B“.
- Empfehlung: Platzierungen von Anfang an ins Datenmodell nehmen, weil ein späterer Wechsel vom Parent-Feld ein Umbau wäre; die Bedienung für „übertragen“ kann später kommen. Zur Vereinfachung: ein Knoten höchstens einmal je Baum.

### Decided

- Nichts wird kopiert; es gibt „umhängen“ und „übertragen“ (Owner).

### Open

- Platzierungen statt Parent-Feld von Anfang an: Vorschlag, wartet auf den Owner.
- Ein Knoten höchstens einmal je Baum und Summen ohne Doppelzählung: Vorschlag, wartet auf den Owner.
- Zwei Aktionen „hier entfernen“ und „Knoten löschen“: Vorschlag, wartet auf den Owner.

## 2026-11-13 — Anker erst nach Erstellen, Sammlung der offenen Grundsatzfragen

### Discussed

- Open vom 2026-11-13 („Anker“ an einem Item ohne eigenen Knoten) geklärt: erst nach „Erstelle“.
- Der Owner fragt, welche grundsätzlichen Fragen noch offen sind. Zusammenstellung, getrennt nach Einfluss auf das Datenmodell:
  - Datenmodell: die drei Vorschläge zu Platzierungen (noch unbeantwortet); Markdown-Spiegel für die Mindmap; Verhältnis zu Topics und Memos; Zugehörigkeit der freien Maps.
  - Später entscheidbar: Form der KI-Vorschläge, Anzeige abgeschlossener Items, Überführen einer Idee ins Backlog, Zukunft des Felds Area, Markierung für Ideen-Knoten, Qualität der runden Anordnung.
- Neu aufgenommen: Markdown-Spiegel (Cloud-Sitzungen arbeiten auf den Dateien; ohne Dateiformat kann die KI dort nicht zuordnen), Zugehörigkeit freier Maps, Feld Area, Markierung für Ideen-Knoten.

### Decided

- „Anker“ erst nach „Erstelle“ (Owner).

### Open

- Die oben genannten Grundsatzfragen; sie stehen im Kopf.
