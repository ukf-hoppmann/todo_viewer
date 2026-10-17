# Synthetische alte Datenbank für die Datenübernahme (`STORY-082`)

Die Datenbank wird nicht als Datei abgelegt, sondern von `tests/helpers/server/legacy_db.py` erzeugt (Schema des alten
Viewers, Daten als Python-Tabellen). Nichts davon stammt aus echten Daten.

Fälle:

- **Projekte:** `Viewer` (Spiegel-Ordner, Auto-Sync), `Zwei` (Spiegel abgeschaltet), `Allgemein` (wird das eingebaute
  Projekt). Dasselbe Label (`TASK-001`, `NOTE-001`) kommt in zwei Projekten vor.
- **Items:** Prioritäten `High`, `dringend`, leer, `Low`, `Medium`, `Prospective`, `Important`, `wichtig`, `Urgent`;
  Archiv (`location = archive`), Papierkorb, fehlender Parent, Abhängigkeit mit und ohne Ziel, Bereiche,
  Zusatzfelder (mit und ohne vorhandene Notizen), Dokumente mit und ohne Namensliste.
- **Topics und Notes:** Topic-Baum mit Termin, gelöschtes Topic, Note mit Topic, zurückgestellt, erledigt (Archiv),
  gelöscht, Dokumente (eines ohne Note).
- **Verknüpfungen:** Rollen `reference`, `origin`, `trigger`; Ziele Item, Note, Topic, anderes Projekt, ein
  unauflösbares Ziel und eine doppelte Verknüpfung.
- **Auslöser:** Zeit (offen, gefeuert), Ereignis (mit und ohne Verknüpfung), Topic-Termin.
- **Hinweise:** an eine Note, an ein Item (entschieden), „Projekt nicht erreichbar“.
- **Zähler:** `note`, `topic`, ein unbekannter.
