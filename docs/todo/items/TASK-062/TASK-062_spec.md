# TASK-062 — Spec: Freie Maps je Projekt

Gesamtbild: `STORY-102_spec.md`; Konzept: `EPIC-008_spec.md`. Der Weg steht in `TASK-062_notes.md`.

## Umfang

- Ein Projekt hat seinen Projektbaum (genau einer, nicht löschbar) und beliebig viele freie Maps. Das Datenmodell
  sieht das schon vor: Bäume haben eine Art, der Projektbaum ist je Projekt einmalig, freie Maps dürfen mehrfach
  vorkommen. Übergreifendes kommt in das eingebaute Projekt „Allgemein“.
- Server und Oberfläche führen mehrere Bäume je Projekt. Eine freie Map hat einen Namen; sie lässt sich anlegen,
  auswählen, umbenennen und löschen, über Oberfläche, API und MCP.
- Es gibt keine Map je Memo. Ein Memo wird an einen Knoten verlinkt, auch in freien Maps; die Map selbst ist kein Ziel einer Verknüpfung.

## Oberfläche

- Die Seitenleiste bekommt den Abschnitt „Maps in <Projekt>“: der Projektbaum zuerst, dann die freien Maps, je mit
  Knotenzahl; „+ Neue Map“; Umbenennen und Löschen über das Kontextmenü eines Eintrags. Mockup:
  https://claude.ai/artifact/3qoj9AET4gmLVxg4Nx8gGw (Variante A).
- Die Gesamtansicht zeigt nur Projektbäume; freie Maps stehen dort nicht.

## Löschen einer freien Map

- Die Map geht in den Papierkorb und lässt sich wiederherstellen. Knoten, die nur in dieser Map stehen, gehen mit.
- Übertragene Äste, die auch in einem anderen Baum stehen, bleiben dort unverändert (Platzierungen sind
  gleichberechtigt); die Rückfrage nennt, wie viele Äste anderswo erhalten bleiben (greift, sobald `TASK-063` Äste
  überträgt).
- Items an gelöschten Knoten fallen an den Parent-Knoten zurück, sonst nach „Nicht zugeordnet“ (Regel aus
  `STORY-100_spec.md`).
- Der Projektbaum lässt sich nicht löschen.

## Festlegungen der Umsetzung

- Der Name einer freien Map ist eine Zeile, höchstens 100 Zeichen und je Projekt eindeutig (ohne Groß-/Kleinschreibung);
  Maps im Papierkorb zählen nicht. Beim Wiederherstellen muss der Name frei sein.
- Eine gelöschte Map erscheint als eigener Eintrag im Papierkorb von `workspace`; Wiederherstellen holt die Knoten zurück,
  die mit ihr gingen.

## Nicht Teil

- Umhängen und Übertragen zwischen Bäumen: `TASK-063`.
- Die Seitenansicht „Nicht zugeordnet“ gibt es nur im Projektbaum, nicht in freien Maps.
