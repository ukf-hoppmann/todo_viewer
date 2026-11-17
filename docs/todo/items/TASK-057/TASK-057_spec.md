# TASK-057 — Spec: Mindmap-Oberfläche für Zahl, Ring, Zustand und Seitenansicht

Fachliche Regeln: `STORY-100_spec.md`. Der Server liefert die Zahlen (`TASK-056`).

## Umfang

- Knotendarstellung: Ideen gestrichelt und hohl; Knoten mit Items zeigen Ring und Zahl; erledigte gedimmt.
- Filter über die Zustände Idee, geplant, in Arbeit, erledigt; er blendet Knoten aus.
- Zahl, Ring und Detail folgen dem Statusfilter des Backlogs (erledigte Items sichtbar oder nicht). Der Zustand
  selbst bleibt davon unberührt.
- Detail eines Knotens: Items und verlinkte Memos; Memos zählen nicht in der Zahl. Zuordnung im Detail eines Knotens
  und eines Items setzen und lösen.
- Seitenansicht „Nicht zugeordnet“ (kein Knoten): listet Items ohne Knoten, Drag-and-drop in den Baum ordnet zu,
  ausschaltbar, nicht im Baum gezählt. Vorbild im Aufbau: „Entfernt“ im Formular-Editor.
- Items im Papierkorb erscheinen nirgends.

## Nicht Teil

Server (`TASK-056`), Markierungen (`TASK-065`).
