# TASK-063 — Spec: Äste umhängen und übertragen

Gesamtbild: `STORY-102_spec.md`; Konzept: `EPIC-008_spec.md`. Der Weg steht in `TASK-063_notes.md`.
Setzt die freien Maps aus `TASK-062` voraus. Entfernte Platzierungen wieder einsetzen: `TASK-066`; Papierkorb-Ansicht:
`NEW-papierkorb-ansicht`.

## Begriffe

- **Umhängen:** aus A weg, in B drin; auch innerhalb eines Baums. **Übertragen:** derselbe Ast in A und B; nur
  zwischen Bäumen. Beides nur innerhalb eines Projekts. Nichts wird kopiert; ein „Trennen“ gibt es nicht.
- Ein Ast ist ein Knoten mit seinen Unterknoten; er hat je Baum eine Platzierung.

## Server

- Umhängen und Übertragen als Operationen mit API und MCP-Werkzeug. Das Ziel ist die Wurzel der Ziel-Map; die
  Position darunter ändert man danach wie gewohnt innerhalb des Baums.
- Abgelehnt werden mit Fehlercode und Liste der betroffenen Knoten: ein Ziel, in dem der Ast oder ein Unterknoten
  schon steht; Kreise; ein Ziel in einem anderen Projekt; die Wurzel einer Map als Quelle; ein Knoten im Papierkorb;
  Übertragen in denselben Baum. Kein Zusammenführen.
- Gemeinsam ist der Inhalt eines übertragenen Knotens (Titel, Text, Notizen, Items). Die Struktur darunter gehört je
  Baum: Ein neuer Unterknoten entsteht in allen Bäumen, in denen sein Parent steht; Umhängen und Entfernen darunter
  gelten nur im bearbeiteten Baum.
- Zahl, Fortschritt und Zustand werden je Baum aus der dort sichtbaren Struktur berechnet und können abweichen. Ein
  Item zählt höchstens einmal; eine Doppelzählung unter einer Wurzel kann nach diesen Regeln nicht entstehen und wird
  nur getestet.
- „Hier entfernen“ nimmt den Ast nur aus einem Baum, „Knoten löschen“ überall; beides getrennt in API und MCP.
  Verliert ein Knoten seine letzte Platzierung, kommt er mit den heimatlos gewordenen Unterknoten in den Papierkorb;
  Unterknoten, die noch in einem anderen Baum stehen, bleiben dort. Items folgen der Regel aus `STORY-100_spec.md`.
- Ein Knoten im Papierkorb lässt sich „wiederherstellen und umziehen“ in einem Schritt, auch über API und MCP. Die
  neue Stelle ersetzt seine alte Platzierung im aktuellen Baum, Platzierungen in anderen Bäumen kommen wie vorher
  zurück.

## Oberfläche

- Kontextmenü am Knoten: „Umhängen nach …“ und „Übertragen nach …“ mit Wahl der Ziel-Map; zusätzlich Ziehen auf
  einen Eintrag der Map-Liste, danach die Wahl „Umhängen“ oder „Übertragen“. Nicht erlaubte Ziele sind ausgegraut mit
  Grund.
- Steht ein Knoten nur in einem Baum, gibt es nur „Löschen“; sonst „Hier entfernen“ (ohne Rückfrage) und „Knoten
  löschen“ (Rückfrage mit den betroffenen Bäumen).
- Markierung: ein Symbol mit der Zahl der Bäume erscheint beim Überfahren und bietet die Bäume zum Springen an; ein
  Schalter in den Filtern färbt alle übertragenen Äste mit einem Rand ein. „Gehe hin“ zu einem Knoten in mehreren
  Bäumen fragt per Auswahl nach dem Baum.

## Nicht Teil

- Wieder einsetzen entfernter Platzierungen: `TASK-066`. Seitenansicht „Papierkorb“ und Ziehen daraus:
  `NEW-papierkorb-ansicht`.
- Dateiformat für den Spiegel: `STORY-105`.
