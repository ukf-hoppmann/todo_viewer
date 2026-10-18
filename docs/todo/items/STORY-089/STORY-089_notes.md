# STORY-089 — Wecker als Erinnerung: mehrere Elemente, Erlöschen und Aufräumen nach 24 h

## 2026-10-18 — Wecker als Erinnerung: Entscheidungen

### Discussed

- Wecker wirkten wie Planungselemente: Label sichtbar, Erledigt blieb für immer, doppelte Überschrift Wecker/Element im Detail.
- Für das Aufräumen nach 24 h stand Architektur §2 im Weg: eine Löschung auf einer Seite ist immer ein Konflikt, der Auto-Sync löscht nie.

### Decided

- Erledigt bleibt 24 h sichtbar (mit Rückgängig), dann wird der Wecker endgültig gelöscht, ohne Papierkorb.
- Das Label bleibt als Schlüssel für Markdown-Spiegel und Cloud-Sitzungen, die Oberfläche zeigt es nicht.
- Ein Wecker hat 0..n Elemente; mit Elementen zeigt er diese, ohne Elemente ist er eine freie Erinnerung mit Text als Überschrift; mehrere Elemente als Karten zum Wechseln, das erste offen.
- Ein Wecker mit Elementen erlischt, sobald keins mehr offen ist (alles außer offen zählt: erledigt, verworfen, archiviert, befördert, gelöscht); teilweise geschlossene werden ausgegraut; wird ein Element in den 24 h wieder geöffnet, kehrt der Wecker zurück.
- Architektur §2 ergänzt (Besitzer-Freigabe 2026-10-18): ein Besitzer darf Spiegel-Einträge als kurzlebig kennzeichnen; ihre Löschung in der Datenbank geht ohne Konflikt in die Dateien, auch beim Auto-Sync; eine Löschung in den Dateien bleibt ein Konflikt.
- Ob ein Element offen ist, fragt der Wecker über registry.is_open von workspace; Backlog und Notes melden ihre Prüfung je Typ an. Die Elemente stehen in alarms_targets (geordnet), nicht in den Verknüpfungen von workspace.
