# TASK-056 — Spec: Mindmap-Server

Fachliche Regeln: `STORY-100_spec.md` (Zuordnung, Zählung, Zustand, Memos). Hier nur, was der Server leistet.

## Umfang

- Zuordnen und Lösen eines Items oder Memos zu einem Knoten über API und MCP. Items: ein zweiter Knoten wird
  abgewiesen oder ersetzt den ersten ausdrücklich. Memos: mehrere Knoten erlaubt.
- Speicherung als `workspace_links` mit eigener Rolle; die Regel „höchstens ein Knoten je Item“ liegt in der Domain.
- Reine Funktion für wirksamen Knoten, Summen ohne Doppelzählung und Zustand; sie kennt leere Knoten und
  eigens angehängte Kinder.
- Zählende Items richten sich nach dem Statusfilter; Papierkorb-Items zählen nie; der Zustand ist filterunabhängig,
  `Rejected` zählt dort nicht (Tabelle in `STORY-100_spec.md`).
- Löschen eines Knotens: Items fallen an den Parent-Knoten, sonst nach „Nicht zugeordnet“; Wiederherstellen stellt
  die Zuordnung wieder her. Memo-Links ruhen im Papierkorb.
- Die Antwort des Baums enthält je Knoten Anzahl, Fortschritt und Zustand sowie die Items ohne Knoten (für die
  Seitenansicht).

## Nicht Teil

Oberfläche (`TASK-057`), Markierungen (`TASK-065`).
