# NEW-settings-gliedern — Einstellungen übersichtlich gliedern: Gruppen, kompakte Projektliste, Sync-Intervall

## State

- Goal/Status: Einstellungen in Gruppen „Projekte“ und „System“ mit Seitennavigation; Backlog angelegt, noch nichts umgesetzt.
- Next step: `NEW-settings-gruppen` umsetzen (Plan vorlegen, Architekturregeln lesen).
- Open:
  - Soll der Abschnitt Auto-Sync später eine eigene Untergruppe unter „System“ bekommen? (2026-11-03)
  - Weitere Kandidaten (Standard-Speicherort für neue Projekte, Startordner des Ordner-Browsers, Markierung im Notes-Baum) gehören zu „Projekte“ bzw. „System“, sind aber nicht Teil dieser Story (2026-11-03)
- Decided:
  - Gruppen „Projekte“ (alles Projektspezifische) und „System“ (Notes, Wecker, Auto-Sync); bei mehr Inhalt wird System feiner gegliedert (2026-11-03)
  - Navigation als Unterrouten mit Seitennavigation links statt einer langen Kartenliste (2026-11-03)
  - Die Sprache bleibt in der Kopfzeile und kommt nicht in die Einstellungen (2026-11-03)
  - Projekte kompakt: Icons mit Tooltips, Detail standardmäßig eingeklappt (2026-11-03)
  - Auto-Sync-Intervall ist in der Oberfläche einstellbar; `AUTO_SYNC_INTERVAL` gewinnt und sperrt das Feld (2026-11-03)
- References: Items NEW-settings-gruppen, NEW-settings-projektliste, NEW-settings-intervall-server, NEW-settings-intervall-ui

State confirmed after entry 2026-11-03 — Aufteilung der Einstellungen (910d82bb2ca2)

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
