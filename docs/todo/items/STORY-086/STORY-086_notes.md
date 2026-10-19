# STORY-086 — Baum: Umwandeln-Dialog beim Ziehen

## 2026-10-19 — Planung Umwandeln-Dialog

### Discussed

- Heute lehnt placementOf unzulässige Stellen mit null ab; retypeItem gibt es schon

### Decided

- Die Regeln werden zu einer Tabelle Zielstelle -> erlaubter Typ; placementOf liefert {parent, position, retypeTo?} oder einen Ablehnungsgrund.
- Ablauf bei Ja: erst retype, dann move; schlägt move fehl, wird der Typ zurückgewandelt und der Fehler gemeldet.
- Eine Story mit Kindern wird nicht zum Task: Ablehnung mit Grund, keine Frage.

### Open

- Ob Task als Wurzel erlaubt ist, ist an den Lifecycle-Regeln zu prüfen.

## 2026-10-19 — Strukturregeln und Typwechsel im Teilbaum

### Discussed

- Harness-Format: Epic ohne Parent; Story unter Epic oder allein; Task unter Story, direkt unter Epic oder allein; unter einem Task nichts; Story unter Story nicht vorgesehen. Der Server prüft heute nur epic_with_parent.
- Üblich in Scrum-Tools: Epic -> Story -> Task, Epics nicht geschachtelt, Tasks allein oder am Epic.
- Bei jedem Ebenenwechsel fragen oder nur, wenn ein Typwechsel nötig ist.

### Decided

- Ein Typwechsel ist nur erlaubt, wenn danach der ganze Teilbaum passt (Item, Kinder, Kindeskinder). Epic -> Story: Kind-Storys werden Tasks, Kind-Tasks bleiben; nicht möglich, wenn eine Kind-Story selbst Kinder hat. Epic -> Task und Story -> Task nur ohne Kinder. Upgrades nur, wenn das Item danach an einer zulässigen Stelle steht.
- Die Strukturregeln (kein Kind unter einem Task, keine Story unter einer Story, Epic ohne Parent) liegen in der Server-Domain und gelten für Anlegen, Verschieben und Typwechsel über API, MCP und UI.
- Gefragt wird nur, wenn ein Typwechsel nötig ist; geht es ohne, wird ohne Rückfrage umgehängt. Der Dialog nennt alle betroffenen Items mit altem und neuem Label. Für das LLM: Fehler retype_required mit den nötigen Änderungen, Wiederholung mit allow_retype.
- Typ ändern im Detailpanel nutzt dieselben Regeln (Upgrade und Downgrade mit Vorschau des Teilbaums, sonst Ablehnung mit Grund).
- Typwechsel im Teilbaum und Verschieben laufen serverseitig in einer Transaktion; das frühere Vorgehen erst retype, dann move im Client entfällt.

## 2026-10-19 — Abschlusskriterien an die Spec angepasst

### Decided

- Abschlusskriterien auf Wunsch des Projektinhabers an die Spec vom 2026-10-19 angepasst.
