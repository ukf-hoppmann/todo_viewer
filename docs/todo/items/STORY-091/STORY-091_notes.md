# STORY-091 — Fällige Wecker in der Projektleiste: globaler und projektbezogener Wecker-Button mit Liste

## 2026-10-19 — Abstimmung Wecker-Liste

### Discussed

- Das Warndreieck in der Projektzeile ist die Sync-Warnung, nicht die Wecker.
- Das Popup der fälligen Wecker (AlarmCounter, ⏰n in der App-Leiste) zeigt die Liste bereits, aber ohne Sortierung, Aufklappen und Sprung zum Element; das Notes-Popup springt beim Klick schon.

### Decided

- Der Wecker-Button öffnet immer eine Liste, auch bei einem Eintrag.
- Der zuletzt ausgelöste Wecker steht oben und ist aufgeklappt, damit ein ignorierter Wecker einen neuen nicht verdeckt.
- Globaler Zähler bleibt, aber als Wecker-Icon im Kopf „Projekte“ statt in der App-Leiste.
- Globale und projektbezogene Liste sind eine Komponente; die projektbezogene filtert über listAlarms(projects, dueOnly).

## 2026-10-19 — Wecker und fällige Notes zusammen

### Discussed

- Notes werden nicht über verknüpfte Wecker fällig, sondern über eigene Gründe: Auslöser (Ereignis), Hinweis, Topic-Termin, Prüfdatum. Nur die letzten beiden hängen an der Uhr.
- Aus Nutzersicht wollen beide jetzt Aufmerksamkeit.

### Decided

- Wecker und fällige Notes werden in der Oberfläche gemeinsam angezeigt (eine Glocke, eine Liste); Daten und Plugins bleiben getrennt.
- !n zieht wie ⏰n aus der App-Leiste in den Kopf „Projekte“.
- Sortierung nach „fällig seit“; für Notes liefert der Server diese Zeit, abgeleitet aus fired_at, created_at des Hinweises, due_at des Topics bzw. review_at.
- Die bisherige Gruppierung der Notes nach Grund wird zu einer Beschriftung in der Zeile.
