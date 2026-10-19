# STORY-086 — Baum: Umwandeln-Dialog beim Ziehen

## Was und warum

Die Struktur Epic → Story → Task gilt heute nur teilweise: Der Server prüft nur „Epic ohne Parent“, der Baum
verbietet zusätzlich „kein Kind unter einem Task“. Eine Story lässt sich heute unter eine Story ziehen, und über
API und MCP kann ein Agent jede Struktur bauen. Diese Story legt die Strukturregeln in die Server-Domain, so dass
sie für UI, API und MCP gleich gelten. Steht ein Item nach einem Verschieben oder Typwechsel an einer Stelle, an der
sein Typ nicht erlaubt ist, wird es samt Teilbaum umgewandelt, aber nur nach Bestätigung.

Entscheidungen: Notizen dieser Story vom 2026-10-19 („Planung Umwandeln-Dialog“, „Strukturregeln und Typwechsel im
Teilbaum“). Die spätere Notiz gilt, wo sie der früheren widerspricht (kein Ablauf „erst retype, dann move“ im
Client).

## Strukturregeln (Server-Domain)

Wie im Harness-Format und in Scrum-Tools üblich:

| Typ | Darf stehen |
|---|---|
| Epic | nur als Wurzel |
| Story | als Wurzel oder unter einem Epic |
| Task | als Wurzel, unter einem Epic oder unter einer Story |

Daraus folgt: unter einem Task steht nichts, Epics und Storys werden nicht geschachtelt.

- Neue Verletzungen neben `epic_with_parent`: `story_with_invalid_parent` (Story unter Story oder Task) und
  `child_of_task` (irgendein Item unter einem Task). Texte in `lifecycle.py` wie die vorhandenen.
- Sie stehen in `LifecycleRules._structure` und gelten über `check_change` für Anlegen, Ändern, Verschieben,
  Typwechsel, Wiederherstellen und den Abgleich aus dem Spiegel, so wie `epic_with_parent` heute.
- `check_change` meldet nur Verletzungen, die eine Änderung neu einführt. Ein Backlog, der die Regeln schon
  verletzt (z. B. in einem anderen Projekt), blockiert deshalb nichts, was die Verletzung nicht berührt.

## Typwechsel im Teilbaum

Ein Typwechsel ist nur erlaubt, wenn danach der ganze Teilbaum passt: das Item, seine Kinder und Kindeskinder.

| Wechsel | Nachfahren | Nicht möglich, wenn |
|---|---|---|
| Epic → Story | Kind-Storys werden Tasks, Kind-Tasks bleiben Tasks | eine Kind-Story selbst Kinder hat |
| Epic → Task | – | das Epic Kinder hat |
| Story → Task | – | die Story Kinder hat |
| Task → Story | – | es danach unter einer Story oder einem Task stünde |
| Story → Epic, Task → Epic | – | es einen Parent hat (Epic nur als Wurzel) |

- Die Domain-Funktion bekommt die Items des Projekts, das Item, den Ziel-Parent (unverändert oder neu) und den
  gewünschten Typ (oder keinen) und liefert entweder den Plan, also die Liste `{uid, label, from_type, to_type}`
  aller nötigen Typwechsel (leer, wenn keiner nötig ist), oder den Grund, warum es nicht geht (Code und betroffene
  Items).
- Ohne gewünschten Typ (reines Verschieben) wählt sie den Typ, der am Ziel passt und den geringsten Eingriff
  braucht: Ist der jetzige Typ erlaubt, bleibt er; sonst gibt es die Auswahl der möglichen Typen (siehe Dialog).
- Gezählt werden alle Nachfahren, auch abgeschlossene und solche im Papierkorb, damit Archiv und Wiederherstellen
  nicht später an den Regeln scheitern.
- Jedes umgewandelte Item bekommt wie beim heutigen `retype_item` ein neues Label, seine Dokumente werden
  umbenannt, und Verweise im Projekt folgen.

## Schnittstellen

- **Verschieben** (`move_item`, API und MCP) bekommt `allow_retype` (Standard `false`) und optional `type` (der
  gewünschte Typ des verschobenen Items).
  - Geht es ohne Typwechsel, wird verschoben wie heute.
  - Braucht es einen Typwechsel und `allow_retype` ist `false`, ändert sich nichts. Antwort: Fehler
    `retype_required` mit `details.options`, je möglichem Zieltyp der Plan (Liste wie oben). Mit nur einer Option
    ist es eine.
  - Mit `allow_retype = true` (und bei mehreren Optionen `type`) werden alle Typwechsel und das Verschieben in
    **einer** Transaktion ausgeführt. Die Antwort nennt alle umgewandelten Items mit altem und neuem Label.
  - Geht es gar nicht, Fehler mit Grund (z. B. `child_of_task`, `retype_breaks_children` mit den Kindern).
- **Typwechsel** (`retype_item`, API und MCP) nutzt dieselbe Domain-Funktion: Muss der Teilbaum mit umgewandelt
  werden, ist das ohne `allow_retype` ebenfalls `retype_required` mit dem Plan, mit `allow_retype` wird alles in
  einer Transaktion umgewandelt.
- **Vorschau** ohne Änderung: eine lesende Operation (API und MCP, z. B. `plan_restructure`) mit Item, Ziel-Parent,
  Position und optional Typ; sie liefert dasselbe wie die Fehlerantwort, auch „kein Typwechsel nötig“. Der Client
  nutzt sie für den Dialog.
- Tool-Beschreibungen für MCP erklären die Regeln, `retype_required` und `allow_retype`, damit ein Agent den Plan
  dem Projektinhaber nennen kann, bevor er bestätigt.
- `docs/techdocs/interfaces.md` und `neubau-server.md` beschreiben Regeln, Fehler und Parameter;
  `neubau-client.md` den Dialog.

## Oberfläche

- **Baum** (`client/src/plugins/backlog/`): `placementOf` rechnet weiter Parent und Position. Erlaubt der Baum
  einen Drop, fragt er die Vorschau ab.
  - Kein Typwechsel nötig: Es wird ohne Rückfrage verschoben (z. B. Task von einer Story direkt ans Epic).
  - Typwechsel nötig: Dialog mit den betroffenen Items (altes → neues Label), Knöpfe je Option und „Abbrechen“.
    Beispiele: Epic unter ein Epic → „Zu Story“ / „Zu Task“ (nur möglich ohne Kinder) / „Abbrechen“; Story unter eine
    Story → „Zu Task“ / „Abbrechen“. Eine Option, die nicht geht, ist mit Grund deaktiviert.
  - Geht es gar nicht (unter einen Task), zeigt der Baum den Drop nicht als möglich an.
  - Fehler des Servers stehen wie heute über dem Baum.
- **Typ ändern** im Detailpanel: Upgrade und Downgrade mit denselben Regeln. Wandelt der Wechsel Nachfahren mit
  um, zeigt der Dialog sie vorher; geht er nicht, ist die Option mit Grund deaktiviert. Danach wie heute der
  Hinweis mit altem und neuem Label.

## Tests

- Domain (Test zuerst, `tests/implementation/unit/server/plugins/backlog/domain/`): jede Zeile der beiden
  Tabellen; Epic → Story mit Kind-Story mit Tasks (abgelehnt) und ohne (Kind-Story wird Task); Nachfahren im Archiv
  und im Papierkorb; bestehende Verletzungen blockieren unbeteiligte Änderungen nicht.
- Service/API/MCP: `retype_required` ändert nichts; `allow_retype` führt alles in einer Transaktion aus (Fehler
  mittendrin lässt nichts halb umgebaut); Labels und Verweise folgen; Anlegen einer Story unter einer Story wird
  abgelehnt.
- Client (`tests/implementation/unit/client/plugins/backlog/`): Drop ohne Typwechsel ohne Dialog; Dialog mit
  Optionen, Zustimmung, Abbrechen, deaktivierte Option; Typ ändern mit Teilbaum.
- Der Systemtest des Harness-Ablaufs deckt `retype_required` und `allow_retype` über MCP ab.

## Nicht Teil dieser Story

- Ziehen zwischen Projekten.
- Ein Ja/Nein-Dialog bei erlaubtem Verschieben über Ebenen hinweg („soll der Task Story werden?“): Das geht über
  „Typ ändern“.
