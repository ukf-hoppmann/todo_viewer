# STORY-096 — Einstellungen übersichtlich gliedern: Gruppen, kompakte Projektliste, Sync-Intervall

## State

- Goal/Status: Einstellungen in Gruppen „Projekte“ und „System“ umgesetzt (Navigation, kompakte Projektliste, Auto-Sync-Intervall zur Laufzeit); alle vier Tasks warten auf die Bestätigung des Owners.
- Next step: Owner prüft die Oberfläche und bestätigt die Tasks und die Story.
- Open:
  - Soll der Abschnitt Auto-Sync später eine eigene Untergruppe unter „System“ bekommen? (2026-11-03)
  - Weitere Kandidaten (Standard-Speicherort für neue Projekte, Startordner des Ordner-Browsers, Markierung im Notes-Baum) sind nicht Teil dieser Story (2026-11-03)
- Decided:
  - Gruppen „Projekte“ (alles Projektspezifische) und „System“ (Notes, Wecker, Auto-Sync); bei mehr Inhalt wird System feiner gegliedert (2026-11-03)
  - Navigation links in der Seite, die Gruppe steht in der URL (`?group=`) statt in Unterpfaden, weil die URL-Form der Architektur nur `/<owner>/<name>` kennt (2026-11-03)
  - Die Sprache bleibt in der Kopfzeile und kommt nicht in die Einstellungen (2026-11-03)
  - Projekte als kompakte Zeilen mit Icons und Tooltips, Detail standardmäßig eingeklappt (2026-11-03)
  - Auto-Sync-Takt: in der Datenbank gespeichert (`core_settings`), gilt sofort und nach Neustart; erlaubt sind 0 (aus) und 1 bis 86400 Sekunden; die Umgebungsvariable `AUTO_SYNC_INTERVAL` gewinnt und sperrt das Feld; kein MCP-Tool (2026-11-03)
  - Takt 0 schaltet den Timer wirklich ab (vorher hätte er sich ohne Pause neu gesetzt) (2026-11-03)
- References: Items NEW-settings-gruppen, NEW-settings-projektliste, NEW-settings-intervall-server, NEW-settings-intervall-ui; Doku neubau-server.md und neubau-client.md

State confirmed after entry 2026-11-03 — Umsetzung (b7bdb451748d)

## 2026-11-03 — Aufteilung der Einstellungen

### Discussed

- Die Einstellungsseite ist eine lange Liste von Karten (Projekte, Notes, Wecker). Projekte nehmen viel Platz ein.
- Vorschlag: Gruppen mit Seitennavigation, Projekte kompakt, das Auto-Sync-Intervall (heute nur Umgebungsvariable bzw. `configs/viewer.json`, nur beim Start gelesen) in die Oberfläche.
- Weitere Kandidaten: Standard-Speicherort für neue Projekte, Startordner des Ordner-Browsers, Markierung im Notes-Baum, Anzeige von Port, Datenbankpfad und Log-Einstellungen nur zur Ansicht.

### Decided

- Zwei Gruppen: „Projekte“ für alles Projektspezifische, „System“ für Notes, Wecker und Auto-Sync; später feiner gliedern, wenn mehr kommt.
- Die Sprache bleibt oben in der Kopfzeile; in die Einstellungen kommen nur allgemeinere Dinge.
- Projekte standardmäßig eingeklappt bzw. mit Icons und Tooltips.
- Intervall in der Oberfläche; die Umgebung gewinnt und sperrt das Feld.

### Open

- Eigene Untergruppe für Auto-Sync später.
- Die weiteren Kandidaten sind nicht Teil dieser Story.

## 2026-11-03 — Umsetzung

### Discussed

- Die Gruppen-URL: Unterpfade wie `/core/settings/system` widersprechen der URL-Form der Architektur (jeder Pfadteil beginnt mit der ID des Beitragenden) und brauchen eine Änderung des Routers; Query-Parameter `?group=` ist direkt aufrufbar und braucht keine Regeländerung.
- Wohin mit dem Takt: Konfigurationsdatei oder Datenbank. Die Datenbank ist die einzige Wahrheit (Architektur §2) und die Notes-Einstellungen liegen auch dort.
- Der Layout-Slot `core.sidebar-sections` nimmt nur Widgets von Plugins entgegen; der Core kann dort nichts einhängen, deshalb zeichnet die Einstellungsseite ihre Navigation selbst.

### Decided

- `?group=` statt Unterpfaden; Navigation in der Seite statt im Layout-Slot (Owner hat den Plan freigegeben).
- Der Takt wird in der Tabelle `core_settings` gespeichert (Migration 2 des Core), die Umgebung gewinnt.
- Auto-Sync-Abschnitt gehört dem Plugin `workspace` (dort liegt die Sync-Oberfläche), Gruppe `system`.
- Pfad und letzter Sync stehen im eingeklappten Detail der Projektzeile, nicht in der Zeile (Owner: „nimm das Detail“).

### Open

- Open from 2026-11-03 (Aufteilung): Untergruppe für Auto-Sync bleibt offen.
