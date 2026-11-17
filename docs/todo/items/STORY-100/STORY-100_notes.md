# STORY-100 — Items und Memos an Knoten hängen: Anzahl, Fortschritt und Zustand am Thema

## State

- Goal/Status: Geplant; drei Tasks (TASK-056, TASK-057, TASK-065); offene Punkte werden der Reihe nach geklärt (2026-11-17).
- Next step: Kriterien 1, 2, 5 und Goal anpassen (nach Zustimmung des Owners); danach Spec nachziehen (2026-11-17)
- Open:
  - Kriterien 1, 2 und 5 und das Goal an die Entscheidungen vom 2026-11-17 angleichen: Seitenansicht statt Sammelknoten, Papierkorb, Löschen von Knoten (2026-11-17)
- Decided:
  - „Nicht zugeordnet“ ist kein Knoten, sondern eine berechnete Seitenansicht je Projekt (wie „Entfernt“ im Formular-Editor): sie listet Items ohne Knoten; per Drag-and-drop ordnet man sie Knoten zu; die Seitenansicht lässt sich ausschalten; sie zählt nicht im Baum (2026-11-17)
  - Wird ein Knoten gelöscht, fallen seine Items an den Parent-Knoten zurück, sonst in „Nicht zugeordnet“; Ergebnis, als wäre der Knoten nie da gewesen (2026-11-17)
  - Ein Memo darf an mehrere Knoten verlinkt sein; wandert der Knoten in den Papierkorb, ruht der Link und kommt mit der Wiederherstellung zurück; das Memo bleibt unverändert (2026-11-17)
  - Items im Papierkorb zählen nie (weder Zahl, Ring, Zustand noch Detail); archivierte Items folgen als Completed/Rejected den bestehenden Regeln (2026-11-17)
  - Markierung „verworfen“/„später“ (TASK-065) ist vom abgeleiteten Zustand getrennt: eigene Eigenschaft des Knotens, ändert weder Zustand noch Summen, nur der Filter kann markierte Knoten ausblenden; gilt nicht für Unterknoten; feste Form bleibt in TASK-065 zu klären (2026-11-17)
  - Zustand aus Items samt Unterknoten, unabhängig vom Statusfilter: Idee = keine zählenden Items; Erledigt = alle zählenden Items Completed; In Arbeit = mindestens ein Item In progress oder Awaiting confirmation, oder Completed gemischt mit Open; Geplant = Items vorhanden, alle Open; Rejected-Items zählen nicht, nur Rejected ergibt Idee (2026-11-17)
  - Abgeschlossene Items folgen dem Statusfilter des Backlogs: Zahl, Ring und Detail richten sich danach (2026-11-17)
  - Items sind nie eigene Knoten; ein Knoten zeigt Anzahl und Fortschrittsring, die Items stehen im Detail (2026-11-13)
  - Ein Epic ist in der Regel ein Knoten, aber nicht zwingend; ein Knoten kann mehrere Epics tragen (Beispiel: Usermanagement mit drei Epics) (2026-11-13)
  - Zuordnung: alles erbt vom Parent, außer ein Item ist eigens angehängt; dann zählen es und seine Kinder zum neuen Knoten (2026-11-13)
  - Ein Item hängt an genau einem Knoten; gespeichert als Verknüpfung mit Regel, nicht als Liste, damit mehrere später möglich bleiben (2026-11-13)
  - Der Zustand eines Knotens ist abgeleitet: Idee (keine Items), geplant, in Arbeit, erledigt; ein Filter darüber zeigt, was es gibt und was kommt (2026-11-13)
  - Summen laufen auch über leere Knoten nach oben; jedes Item zählt einmal (2026-11-13)
  - Memos lassen sich an Knoten verlinken und stehen nur im Detail, ohne eigene Zahl am Knoten (2026-11-13)
  - Was die KI nicht zuordnen kann, landet in „Nicht zugeordnet“ (Seitenansicht, siehe 2026-11-17) (2026-11-13)
  - Verworfen: strikte Vererbung vom Wurzel-Item ohne Ausnahme; sie verhindert das Planen unterhalb eines Epic-Knotens (2026-11-13)
- References: Konzept `EPIC-008_spec.md` im Epic `EPIC-008`; Ideensammlung `TASK-064`

State confirmed after entry 2026-11-17 — „Nicht zugeordnet“ und Löschen von Knoten (875695d98238)

## 2026-11-13 — Übernahme der Entscheidungen aus der Ideensammlung

### Discussed

- Die Punkte stammen aus der Ideensammlung im Task `TASK-064`; dort steht der Weg zu den Entscheidungen mit Optionen und Gründen.
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

## 2026-11-17 — Abgeschlossene Items an Knoten

### Discussed

- Frage: Wie werden Completed/Rejected-Items an einem Knoten behandelt?
- Optionen: (a) dem Statusfilter des Backlogs folgen; (b) nur im Fortschritt zählen, nie im Detail; (c) immer zählen und zeigen. Zu (a): bekanntes Verhalten, ohne Filter x von y erledigt. Zu (b): kurzes Detail, aber man sieht Erledigtes nicht. Zu (c): vollständig, aber das Detail wächst mit der Zeit.
- Empfehlung: (a).
- Offene Punkte aus der Durchsicht der Story: Zustandsregel, Markierungen, Papierkorb/Archiv, Memo-Links, Sammelknoten, Löschen von Knoten, Kriterium 1.

### Decided

- Abgeschlossene Items folgen dem Statusfilter des Backlogs: Zahl, Ring und Detail richten sich danach. Grund: ein Verhalten, das der Eigner aus dem Backlog schon kennt.
- Verworfen: nur im Fortschritt zählen; immer zählen und zeigen.

### Open

- Open from 2026-11-13 (Abgeschlossene Items) resolved: siehe oben.
- Zustandsregel, Markierungen, Papierkorb/Archiv, Memo-Links, Sammelknoten, Löschen von Knoten, Kriterium 1: werden der Reihe nach geklärt.

## 2026-11-17 — Zustandsregel des Knotens

### Discussed

- Frage: Wie wird Idee, geplant, in Arbeit, erledigt aus den Items samt Unterknoten abgeleitet?
- Optionen: (a) nach Items, Rejected ignoriert; (b) Rejected zählt wie Completed; (c) In Arbeit erst, wenn ein Item In progress ist. Zu (b): ein verworfenes Thema wirkt wie ein gelungenes. Zu (c): ein halb erledigter Knoten wirkt unbegonnen.
- Empfehlung: (a).

### Decided

- Zustand nach (a), unabhängig vom Statusfilter: Idee = keine zählenden Items; Erledigt = alle zählenden Items Completed; In Arbeit = mindestens ein Item In progress oder Awaiting confirmation, oder Completed gemischt mit Open; Geplant = Items vorhanden, alle Open. Rejected-Items zählen nicht; nur Rejected ergibt Idee.
- Verworfen: Rejected wie Completed; In Arbeit erst ab In progress.

### Open

- Open from 2026-11-17 (Zustandsregel) resolved: siehe oben.
- Markierungen „verworfen“/„später“ (TASK-065) im Verhältnis zum Zustand; Papierkorb/Archiv; Memo-Links; Sammelknoten; Löschen von Knoten; Kriterium 1.

## 2026-11-17 — Markierung und abgeleiteter Zustand

### Discussed

- Frage: Wie verhält sich die Markierung „verworfen“/„später“ (TASK-065) zum abgeleiteten Zustand?
- Optionen: (a) getrennt vom Zustand; (b) Markierung überschreibt den Zustand, dann geht „in Arbeit“ optisch verloren und der Filter vermischt Ableitung und Handeintrag; (c) Unterknoten erben die Markierung, dann können sie sie nicht eigens aufheben.
- Empfehlung: (a), passend zu Kriterium 3 von TASK-065.

### Decided

- Getrennt vom Zustand: eigene Eigenschaft des Knotens, ändert weder Zustand noch Summen; der Filter kann markierte Knoten ausblenden; gilt nur für den Knoten selbst.
- Verworfen: Markierung überschreibt den Zustand; Vererbung an Unterknoten.

### Open

- Feste Werte oder frei: bleibt wie in TASK-065 vor der Umsetzung zu klären.
- Papierkorb/Archiv in den Summen; Memo-Links; Sammelknoten; Löschen von Knoten; Kriterium 1.

## 2026-11-17 — Papierkorb und Archiv in den Knotensummen

### Discussed

- Frage: Wie zählen Items im Papierkorb und archivierte Items?
- Optionen: (a) Papierkorb nie, Archiv wie Completed/Rejected; (b) Archiv zählt immer im Fortschritt, widerspricht aber dem Statusfilter-Beschluss; (c) Papierkorb ausgegraut im Detail, unruhiger und abweichend vom Backlog.
- Empfehlung: (a).

### Decided

- Papierkorb-Items zählen nie, auch nicht im Detail. Archivierte Items sind Completed/Rejected und folgen Statusfilter und Zustandsregel. Kriterium 2 bekommt dazu einen Satz.
- Verworfen: Archiv zählt immer; Papierkorb ausgegraut im Detail.

### Open

- Memo-Links; Sammelknoten; Löschen von Knoten; Kriterium 1.

## 2026-11-17 — Memo-Links an Knoten

### Discussed

- Frage: Wie viele Knoten je Memo, und was geschieht beim Löschen des Knotens?
- Optionen: (a) mehrere Knoten, Link folgt dem Papierkorb; (b) höchstens ein Knoten, eindeutig, aber ein Memo zu zwei Themen braucht einen Umweg; (c) mehrere Knoten, Link beim Löschen endgültig entfernt, Wiederherstellen bringt Links nicht zurück.
- Empfehlung: (a). Memos zählen nicht, daher entfällt der Grund für die Ein-Knoten-Regel der Items.

### Decided

- Mehrere Knoten je Memo; der Link ruht, solange der Knoten im Papierkorb liegt, und kommt bei der Wiederherstellung zurück; das Memo selbst bleibt unverändert.
- Verworfen: höchstens ein Knoten je Memo; Link beim Löschen endgültig entfernen.

### Open

- Sammelknoten; Löschen von Knoten (Items); Kriterium 1.

## 2026-11-17 — „Nicht zugeordnet“ und Löschen von Knoten

### Discussed

- Frage: Wie ist „Nicht zugeordnet“ beschaffen? Optionen: (a) berechnet je Projekt, fest; (b) gespeicherter Knoten; (c) ein Korb über alle Projekte. Empfehlung: (a).
- Der Owner präzisiert (a): kein Knoten, sondern eine Ansicht an der Seite, ähnlich „Entfernt“ im Formular-Editor; dort Drag-and-drop in Knoten; ausschaltbar.
- Frage: Was geschieht mit eigens angehängten Items beim Löschen eines Knotens? Der Owner entscheidet: Rückfall an den Parent-Knoten, sonst „Nicht zugeordnet“, als wäre der Knoten nie da gewesen.

### Decided

- Seitenansicht statt Sammelknoten; je Projekt berechnet; Drag-and-drop zum Zuordnen; ausschaltbar; nicht im Baum gezählt.
- Löschen eines Knotens: Items fallen an den Parent-Knoten, sonst in „Nicht zugeordnet“.
- Verworfen: gespeicherter Knoten; ein Korb über alle Projekte.

### Open

- Kriterien 1, 2, 5 und Goal an die Entscheidungen angleichen (ändert die Bedeutung, daher mit dem Owner).
