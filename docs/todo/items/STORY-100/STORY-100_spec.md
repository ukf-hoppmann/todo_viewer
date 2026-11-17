# STORY-100 — Spec: Items und Memos an Knoten hängen

Der Weg zu den Entscheidungen steht in `STORY-100_notes.md`; das Gesamtkonzept in `EPIC-008_spec.md`.
Umgesetzt wird es in `TASK-056` (Server), `TASK-057` (Oberfläche) und `TASK-065` (Markierungen).

## Zweck

Der Themenbaum wird zur Übersicht des Backlogs: Ein Knoten zeigt nur Zahl, Fortschritt und Zustand seiner Items.
Die Items selbst stehen im Detail des Knotens.

## Zuordnung

- Ein Item hängt an höchstens einem Knoten (Domain-Regel). Gespeichert wird eine Verknüpfung in `workspace_links`
  mit eigener Rolle, kein Feld und keine Liste; mehrere Knoten je Item bleiben so später möglich.
- Wirksamer Knoten eines Items: der eigens zugeordnete, sonst der wirksame Knoten seines Parents. Ein eigens
  angehängtes Item zieht seine Kinder mit. Ein Epic ist in der Regel ein Knoten, aber nicht zwingend; ein Knoten
  kann mehrere Epics tragen.
- Items sind nie eigene Knoten.
- Wird ein Knoten gelöscht (Papierkorb), fallen seine eigens angehängten Items an den Parent-Knoten zurück, sonst
  nach „Nicht zugeordnet“. Das Ergebnis gleicht dem, als wäre der Knoten nie da gewesen. Wird er wiederhergestellt,
  gilt die Zuordnung wieder.

## Zählung

- Ein Knoten zeigt Anzahl und Fortschrittsring über sich und seine Unterknoten. Summen laufen auch über leere
  Knoten nach oben; jedes Item zählt genau einmal.
- Zählende Items: alle Items, die der Statusfilter des Backlogs durchlässt. Ohne Filter zählen erledigte mit
  (x von y erledigt); mit Filter „offen“ fehlen sie in Zahl, Ring und Detail.
- Items im Papierkorb zählen nie, auch nicht im Detail. Archivierte Items sind `Completed` oder `Rejected` und
  folgen Statusfilter und Zustandsregel.

## Zustand eines Knotens

Aus den Items samt Unterknoten abgeleitet, unabhängig vom Statusfilter:

| Zustand | Bedingung |
| --- | --- |
| Idee | keine zählenden Items (nur `Rejected` oder keine Items) |
| Geplant | Items vorhanden, alle `Open` |
| In Arbeit | mindestens ein Item `In progress` oder `Awaiting confirmation`, oder `Completed` gemischt mit `Open` |
| Erledigt | alle zählenden Items `Completed` |

- `Rejected`-Items zählen im Zustand nicht mit.
- Der Zustand ist filterbar; der Filter blendet Knoten aus.

## Memos

- Ein Memo lässt sich an mehrere Knoten verlinken. Es steht nur im Detail und zählt nicht in der Zahl.
- Wandert ein Knoten in den Papierkorb, ruht der Link und kommt mit der Wiederherstellung zurück; das Memo bleibt
  unverändert.

## Seitenansicht „Nicht zugeordnet“

- Kein Knoten, sondern eine berechnete Ansicht je Projekt an der Seite (Vorbild: „Entfernt“ im Formular-Editor).
- Sie listet die Items ohne Knoten; per Drag-and-drop ordnet man sie einem Knoten zu und sie verschwinden dort.
- Sie lässt sich ausschalten. Sie zählt nicht im Baum. Die KI legt Items, die sie nicht zuordnen kann, dort ab.

## Markierung

„verworfen“ und „später“ an Knoten (`TASK-065`): eigene Eigenschaft des Knotens, getrennt vom Zustand. Sie ändert
weder Zustand noch Summen; der Filter kann markierte Knoten ausblenden. Sie gilt nur für den Knoten selbst.

## Rahmen

- Domain-, API- und UI-Tests sind Teil jedes Tasks; die Regeln liegen in reinen Funktionen der Domain.
- Abhängigkeit: `STORY-099` (Gerüst) ist abgeschlossen.

