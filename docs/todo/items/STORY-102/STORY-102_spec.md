# STORY-102 — Spec: Freie Maps und Äste zwischen Bäumen umhängen und übertragen

Der Weg zu den Entscheidungen steht in `STORY-102_notes.md`; das Gesamtkonzept in `EPIC-008_spec.md`.
Umgesetzt wird es in `TASK-062` (freie Maps), `TASK-063` (Umhängen und Übertragen), `TASK-066` (entfernte
Platzierungen merken) und `TASK-067` (Papierkorb-Ansicht). Die beiden letzten sind nicht Pflicht für die Story.

## Maps

- Ein Projekt hat seinen Projektbaum (nicht löschbar) und beliebig viele freie Maps zum Brainstormen. Übergreifendes
  kommt ins eingebaute Projekt „Allgemein“. Eine eigene Map je Memo gibt es nicht; ein Memo wird an einen Knoten
  verlinkt, auch in freien Maps; die Map selbst ist kein Ziel. Die Seitenansicht „Nicht zugeordnet“ gibt es nur im
  Projektbaum. Ein Export einer Map in ein Memo ist nur als Idee im Memo `MEMO-003` festgehalten.
- Auswahl: Liste „Maps“ in der Seitenleiste (Projektbaum zuerst, dann freie Maps); dort auch Anlegen, Umbenennen,
  Löschen. Die Gesamtansicht zeigt nur Projektbäume.
- Löschen einer freien Map: Papierkorb mit Wiederherstellen. Knoten nur dieser Map gehen mit, übertragene Äste
  bleiben im anderen Baum, Items fallen wie bei gelöschten Knoten an den Parent-Knoten oder nach „Nicht zugeordnet“.
  Die Rückfrage nennt, wie viele Äste anderswo erhalten bleiben.

## Umhängen und Übertragen

- Umhängen: aus A weg, in B drin; auch innerhalb eines Baums. Übertragen: derselbe Ast in A und B; nur zwischen
  Bäumen. Beides nur innerhalb eines Projekts. Nichts wird kopiert.
- Bedienung: Kontextmenü „Umhängen nach …“ / „Übertragen nach …“ und Ziehen auf einen Eintrag der Map-Liste mit
  Wahl. Der Ast landet unter der Wurzel der Ziel-Map; die Position danach per Ziehen. Beides auch über API und MCP,
  damit die KI Äste verschieben kann.
- Abgelehnt werden: Ziel, in dem der Ast oder ein Unterknoten schon steht (die Meldung nennt die Knoten; in der
  Oberfläche sind solche Ziele ausgegraut mit Grund, die API liefert einen Fehlercode mit Liste), Kreise, anderes
  Projekt, Wurzel einer Map, Knoten im Papierkorb. Kein Zusammenführen.
- Papierkorb: ein Knoten dort lässt sich „wiederherstellen und umziehen“ (Backend, auch API und MCP); in der
  Oberfläche zieht man ihn aus der Seitenansicht „Papierkorb“ an eine neue Stelle. Die neue Stelle ersetzt seine alte
  Platzierung im aktuellen Baum, Platzierungen in anderen Bäumen kommen wie vorher zurück.

## Gemeinsame Äste

- Inhalt (Titel, Text, Notizen, Items) ist in allen Bäumen gleich; die Struktur darunter gehört je Baum. Ein neuer
  Unterknoten erscheint in allen Bäumen, in denen sein Parent steht; Umhängen und „Hier entfernen“ darunter gelten
  nur im bearbeiteten Baum. Zahl, Fortschritt und Zustand werden je Baum berechnet und können abweichen. Eine
  Doppelzählung unter einer Wurzel kann nicht entstehen; das Kriterium bleibt als Test.
- Markierung: ein Symbol mit der Zahl der Bäume erscheint beim Überfahren und bietet die Bäume zum Springen an; ein
  Schalter in den Filtern färbt alle übertragenen Äste mit einem Rand ein. „Gehe hin“ zu einem Knoten in mehreren
  Bäumen fragt per Auswahl nach dem Baum.
- „Hier entfernen“ nimmt den Ast nur aus diesem Baum, „Knoten löschen“ überall. Steht ein Knoten nur in einem Baum,
  gibt es nur „Löschen“; bei einem geteilten Knoten fragt „Knoten löschen“ mit den betroffenen Bäumen. Verliert ein
  Knoten seine letzte Platzierung, kommt er mit den heimatlos gewordenen Unterknoten in den Papierkorb. Getrennt über
  API und MCP.
- Entfernte Platzierungen bleiben gemerkt und lassen sich wieder einsetzen (`TASK-066`).
