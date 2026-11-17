# ToDo Viewer

Lokaler Dienst mit Web-Oberfläche für Backlogs im Claude_Harness-Format: Epics, Stories und Tasks mit Abhängigkeiten,
Memos mit Wiedervorlage, Wecker und eine Mindmap als Themen-Gerippe. Alles liegt in einer Datenbank; ein Projekt kann
zusätzlich einen Markdown-Ordner als Spiegel führen, den man über Git mitnimmt. KI-Agenten arbeiten über denselben
Dienst per HTTP-API oder MCP.

Technische Dokumentation: [Architektur](docs/techdocs/architecture.md) ·
[Schnittstellen](docs/techdocs/interfaces.md) · [Konfiguration](docs/techdocs/configuration.md) ·
[Betrieb](docs/techdocs/operations.md) · [Server](docs/techdocs/neubau-server.md) ·
[Client](docs/techdocs/neubau-client.md)

## Quickstart (Docker)

```bash
./todo.sh start
```

Baut das Image (falls nötig), startet den Viewer und den nginx-Proxy `todo-proxy` im Hintergrund und öffnet
[http://todo.localhost:5413](http://todo.localhost:5413). Direkt ist der Viewer unter
[http://localhost:5411](http://localhost:5411) erreichbar. Beide Container laufen mit `restart: unless-stopped`
dauerhaft weiter und lauschen nur auf `127.0.0.1`.

```bash
./todo.sh stop      # Container anhalten
./todo.sh restart   # Container neu starten
./todo.sh down      # Container entfernen (configs/ und logs/ bleiben erhalten)
./todo.sh update    # nach Code-Änderungen neu bauen (--no-cache) und ersetzen
./todo.sh logs      # Live-Log (logs/viewer.log)
./todo.sh status    # Container und Antwort von /api/core/health (direkt und über den Proxy)
./todo.sh open      # nur den Browser öffnen
```

Daten und Sicherungen liegen auf dem Host in `configs/` (`viewer.db`, `backups/`), Logs in `logs/`. Details:
[Betrieb](docs/techdocs/operations.md).

## Projekte

Ein Projekt ist ein Arbeitsbereich mit eigenem Backlog, eigenen Memos, Weckern und eigener Mindmap. Die Seitenleiste
listet die Projekte: die Checkbox blendet eines ein oder aus, ein Klick markiert es (ein zweiter hebt auf), Ziehen ordnet
neu, die Suche gilt für alle Seiten. Über **＋** und ✎ legt man ein Projekt an oder öffnet seine Karte (Name,
Spiegel-Ordner, Spiegel, Auto-Sync, Richtung). Die Glocke zählt alles Fällige (Wecker und Memos) und öffnet eine Liste
mit Aktionen. Der DE/EN-Schalter oben übersetzt nur die Anzeige; gespeichert wird mit englischen Werten.

## Spiegel und Sync

Jedes Projekt kann einen Markdown-Ordner als **Spiegel** führen (Format: [Schnittstellen](docs/techdocs/interfaces.md)).
Er wird nur durch einen Sync geschrieben. Der Sync gleicht **Eintrag für Eintrag** ab und zeigt zuerst eine **Vorschau**:
was nur in der Datenbank geändert oder neu ist, geht in den Ordner, was nur im Ordner geändert oder neu ist, in die
Datenbank. Ein Eintrag, der auf beiden Seiten geändert, auf beiden neu oder auf einer Seite gelöscht wurde, ist ein
**Konflikt**: er wird nie überschrieben oder gelöscht, und man entscheidet je Konflikt (Datenbank, Dateien oder später).
Löschungen gehören nie zu den Sammelknöpfen. Die Richtung lässt sich auf eine Seite einschränken. Vor einem Sync in die
Datenbank sichert der Dienst sie.

Der **Auto-Sync** (je Projekt, Standard aus) gleicht nur Konfliktfreies ab, löscht nie und pausiert bei fehlendem Ordner,
Git-Merge-Markern oder laufendem Git-Vorgang. In der Projektliste zeigt ⚠ „braucht dich“ oder „pausiert“, ↻ einen
gespiegelten Projekt. So lassen sich Backlogs über Git zwischen Rechnern und in die Cloud (claude.ai) mitnehmen.

## Backlog

Die Seite „Backlog“ zeigt je sichtbarem Projekt den Baum Epic → Story → Task mit Fortschrittsring und Fortschrittsbalken.
Optionale Kinder (`Required for parent: No`) sind gestrichelt angebunden, gedimmt und zählen ebenso wenig mit wie
abgelehnte. Filter für Status und Priorität stehen in der Seitenleiste; standardmäßig sind `Completed` und `Rejected`
ausgeblendet (sie zählen im Fortschritt). Items lassen sich per Drag-and-drop umhängen; die Struktur (Epic nur als
Wurzel, nichts unter einem Task) prüft der Server.

Im Detail ändern Status, Priorität, Bereich, „Pflicht für Parent“ und Abhängigkeiten sich sofort; „Bearbeiten“ öffnet ein
Formular für alle Felder. `Completed` und `Rejected` fragen nach einer Entscheidung und archivieren das Item. Ein Item
lässt sich mit Kindern anlegen, im Typ ändern (neues Label, Verweise folgen) und in den Papierkorb legen. Notizen und
Specs stehen im Abschnitt „Dokumente“ (Markdown, Großansicht, Notiz-Eintrag anhängen, Spec anlegen); ein Versionskonflikt
bietet „Aktuellen Stand anzeigen“ und „Trotzdem speichern“. Verknüpfungen zeigen, worauf ein Item verweist und was auf
es verweist.

Die Seite „Abhängigkeiten“ zeigt die Abhängigkeiten als gerichteten Graphen (nur Items, die an einer Abhängigkeit
teilnehmen); Auswahl und Hover heben Knoten, Kanten und direkte Nachbarn hervor.

Der **Papierkorb** listet gelöschte Elemente aller Bereiche mit Wiederherstellen und endgültigem Löschen, einzeln oder
gesammelt; gelöschte Notizen und Specs stehen als eigene Zeilen dabei.

## Memos

Memos sind Gedanken mit Wiedervorlage, getrennt vom Backlog: Baum Projekt → Topic → Unter-Topic → Memo. Ein Memo hat
einen Status (wartet, fällig, zurückgestellt, erledigt, verworfen, befördert), ein Prüf-Datum und Auslöser (Item erreicht
einen Status). Fälliges steht in der Glocke, gruppiert nach Grund. Aktionen im Detail: Bearbeiten, Erledigen, Verwerfen,
Zurückstellen, Behalten, Löschen und **Befördern** zu Epic, Story oder Task; ein Item lässt sich zurückstufen. Topics
kann man anlegen, verschieben, archivieren und löschen.

## Wecker

Die Seite „Wecker“ listet Erinnerungen, gruppiert nach Fällig, Heute, Später, Erledigt. Ein Wecker erinnert an ein oder
mehrere Elemente oder an einen freien Text, lässt sich bearbeiten, zurückstellen und erledigen und kann sich
wiederholen. Fällige Wecker erscheinen als Banner und, wenn erlaubt, als Browser-Benachrichtigung.

## Mindmap

Die Seite „Mindmap“ zeigt den Themenbaum **eines** Projekts als Map zur Seite: das Projekt ist die Wurzel, Unterthemen
folgen rechts. Man legt Themen an (Doppelklick benennt um), klappt Äste auf und zu, zieht sie samt Unterthemen an eine
andere Stelle und schreibt Notizen und Specs an ein Thema. Backlog-Items und Memos lassen sich an ein Thema hängen: es
zeigt dann Zahl und Fortschrittsring seiner Items samt Unterthemen und einen daraus abgeleiteten Zustand (Idee, geplant,
in Arbeit, erledigt); die Items selbst stehen nur im Detail. Items ohne Thema stehen in der Seitenansicht „Nicht
zugeordnet“ und werden von dort auf ein Thema gezogen. Die Markierungen „verworfen“ und „später“ lassen alte Ideen als
Spur stehen; Zustand und Markierung lassen sich in der Seitenleiste ausblenden.

## Nutzung durch Agenten

Agenten pflegen Backlog, Memos, Wecker und Mindmap über den Dienst statt über die Dateien: per MCP unter
`http://localhost:5411/mcp` (je Operation ein Tool `<plugin>_<operation>`) oder per HTTP unter `/api/<plugin>/…`. Der
Server prüft die Regeln des Backlog-Formats, schreibende Aufrufe tragen ein Versionstoken, und dauerhaftes Löschen sowie
Einstellungen gibt es nicht als Werkzeug. Der Port ist nur lokal erreichbar. Einzelheiten:
[Schnittstellen](docs/techdocs/interfaces.md).

## Entwicklung

```bash
scripts/check-next.sh   # Server: ruff, mypy, import-linter, pytest; Client: tsc, eslint, vitest
```

Ohne Docker: Server mit `PYTHONPATH=server/src python -m viewer.app.main` (Port 5411), Client mit `cd client && npm run
dev` (Port 5173). Aufbau und Befehle: [Server](docs/techdocs/neubau-server.md), [Client](docs/techdocs/neubau-client.md);
Tests: `tests/README.md`; verbindliche Regeln: `docs/development/architecture.md`.
