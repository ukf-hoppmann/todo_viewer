# NEW-mm-zuordnung — Items und Memos an Knoten hängen: Anzahl, Fortschritt und Zustand am Thema

## State

- Goal/Status: Geplant; zwei Tasks angelegt.
- Next step: Nach dem Gerüst mit dem Server-Task beginnen.
- Open:
  - Abgeschlossene Items: nur im Fortschritt zählen oder im Detail auch zeigen; Vorschlag ist, dem Statusfilter des Backlogs zu folgen (2026-11-13)
- Decided:
  - Items sind nie eigene Knoten; ein Knoten zeigt Anzahl und Fortschrittsring, die Items stehen im Detail (2026-11-13)
  - Ein Epic ist in der Regel ein Knoten, aber nicht zwingend; ein Knoten kann mehrere Epics tragen (Beispiel: Usermanagement mit drei Epics) (2026-11-13)
  - Zuordnung: alles erbt vom Parent, außer ein Item ist eigens angehängt; dann zählen es und seine Kinder zum neuen Knoten (2026-11-13)
  - Ein Item hängt an genau einem Knoten; gespeichert als Verknüpfung mit Regel, nicht als Liste, damit mehrere später möglich bleiben (2026-11-13)
  - Der Zustand eines Knotens ist abgeleitet: Idee (keine Items), geplant, in Arbeit, erledigt; ein Filter darüber zeigt, was es gibt und was kommt (2026-11-13)
  - Summen laufen auch über leere Knoten nach oben; jedes Item zählt einmal (2026-11-13)
  - Memos lassen sich an Knoten verlinken und stehen nur im Detail, ohne eigene Zahl am Knoten (2026-11-13)
  - Was die KI nicht zuordnen kann, landet in einem Sammelknoten „Nicht zugeordnet“ (2026-11-13)
  - Verworfen: strikte Vererbung vom Wurzel-Item ohne Ausnahme; sie verhindert das Planen unterhalb eines Epic-Knotens (2026-11-13)
- References: Konzept `NEW-mindmap_spec.md` im Epic `NEW-mindmap`; Ideensammlung `NEW-mindmap-machbarkeit`

State confirmed after entry 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung (0125fb929825)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `NEW-mindmap-machbarkeit`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.
- Geplante Wiederverwendung: Verknüpfungen über `workspace_links` mit einer eigenen Rolle; die Regel „höchstens ein Knoten je Item“ liegt in der Domain.

### Decided

- Items sind nie eigene Knoten; ein Knoten zeigt Anzahl und Fortschrittsring, die Items stehen im Detail
- Ein Epic ist in der Regel ein Knoten, aber nicht zwingend; ein Knoten kann mehrere Epics tragen (Beispiel: Usermanagement mit drei Epics)
- Zuordnung: alles erbt vom Parent, außer ein Item ist eigens angehängt; dann zählen es und seine Kinder zum neuen Knoten
- Ein Item hängt an genau einem Knoten; gespeichert als Verknüpfung mit Regel, nicht als Liste, damit mehrere später möglich bleiben
- Der Zustand eines Knotens ist abgeleitet: Idee (keine Items), geplant, in Arbeit, erledigt; ein Filter darüber zeigt, was es gibt und was kommt
- Summen laufen auch über leere Knoten nach oben; jedes Item zählt einmal
- Memos lassen sich an Knoten verlinken und stehen nur im Detail, ohne eigene Zahl am Knoten
- Was die KI nicht zuordnen kann, landet in einem Sammelknoten „Nicht zugeordnet“
- Verworfen: strikte Vererbung vom Wurzel-Item ohne Ausnahme; sie verhindert das Planen unterhalb eines Epic-Knotens

### Open

- Abgeschlossene Items: nur im Fortschritt zählen oder im Detail auch zeigen; Vorschlag ist, dem Statusfilter des Backlogs zu folgen
