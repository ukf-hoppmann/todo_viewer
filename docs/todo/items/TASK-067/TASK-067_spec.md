# TASK-067 — Spec: Papierkorb-Ansicht

Gesamtbild: `STORY-102_spec.md`. Der Weg steht in `TASK-067_notes.md`. Setzt `TASK-063` voraus.

## Umfang

- Eine Seitenansicht „Papierkorb“ neben der Karte zeigt die gelöschten Knoten des Projekts. Sie lässt sich wie
  „Nicht zugeordnet“ ein- und ausschalten.
- Man zieht einen Knoten aus der Seitenansicht an eine Stelle der Karte; er wird dort mit seinen Unterknoten
  reaktiviert. Das Backend ist „wiederherstellen und umziehen“ aus `TASK-063`.
- Gezeigt werden die gelöschten Äste der gezeigten Map (oberster gelöschter Knoten je Ast, mit der Zahl seiner Knoten);
  der Schalter ist standardmäßig aus, die Ansicht gibt es nur in der Einzelansicht. Lesend dafür: `list_trashed_nodes`.
- Die neue Stelle ersetzt seine alte Platzierung im aktuellen Baum; Platzierungen in anderen Bäumen kommen wie vorher
  zurück. Nicht erlaubte Stellen werden wie beim Umhängen abgelehnt.

## Nicht Teil

- Das Wiederherstellen ohne Umziehen bleibt im Workspace-Papierkorb.
- Entfernte Platzierungen wieder einsetzen: `TASK-066`.
