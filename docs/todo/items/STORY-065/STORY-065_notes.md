# STORY-065 — Generischer Sync-Dienst über Datenbank und Dateien

## 2026-10-16 — Entscheidungen

### Decided

- Markdown bleibt als Spiegel mit Sync, weil in der Cloud nur mit .md gearbeitet werden kann; Cloud-Einträge werden lokal eingesammelt und in die DB übernommen.
- Der Sync muss später abschaltbar sein, ohne dass die Plugins es merken.
- Zuordnung nur über die UUID; das Label ist Anzeige.
- Zwei Infrastrukturen (Datenbank, Dateien); der Sync ist ein Dienst über beiden Ports.

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Ein Lauf je Projekt über alle spiegelnden Plugins.** `core_sync_state` hat keine Spalte für den Besitzer; der Sync arbeitet deshalb je Projekt mit allen Spiegeln zusammen (geordnet nach `requires`), nur dann ist die Aufräumregel „Basis-Zeile, die auf keiner Seite mehr vorkommt“ eindeutig. Die Spiegel kommen aus `PluginDefinition.mirror`, einer Funktion `services -> MirrorBinding(codec, participant)`.
- **Hash eines Eintrags** = SHA-256 von Art, Feldern und Verweisen; das Label gehört nicht dazu. Labels vergibt nur die Datenbank, ein von Hand geändertes Label in der Datei ist keine Änderung und wird beim nächsten Schreiben des Eintrags überschrieben. Verweise stehen als Labels in `MirrorEntry.refs` (getrennt von den übrigen Feldern), damit der Sync sie umschreiben kann (Platzhalter → Label, altes Label → aktuelles Label über `SyncParticipant.resolve_labels`).
- **Löschungen.** „Auf einer Seite gelöscht“ ist immer ein Konflikt (`deleted_in_files`, `deleted_in_database`). Wer die Löschung durchführen will, entscheidet das je Konflikt und bestätigt zusätzlich mit `delete_missing=true`; ohne das Flag wird eine solche Entscheidung abgewiesen. Siehe Frage 17 in `STORY-060`.
- **Reihenfolge eines Laufs.** Plan berechnen → Token prüfen → Backup (Grund `sync`) → eine Datenbank-Transaktion für alle Teilnehmer (Labels vergeben, Platzhalter ersetzen, `apply`) → Dateien schreiben (mit den beim Lesen erfassten Versionen, sonst `mirror_conflict`) → Dateien neu lesen und für jeden Eintrag, der beidseitig gleich ist, den Basis-Hash setzen → Ereignis `core.sync.state`. Schlägt das Schreiben der Dateien nach dem Commit fehl, bleibt die Datenbank richtig und der nächste Lauf holt auf.
- `assign_labels` bekommt zusätzlich die Transaktion (die Zähler liegen in der Datenbank und müssen mit den Einträgen zusammen festgeschrieben werden). Siehe Frage 18.
- Neue Einträge aus den Dateien werden nur bei Richtung `both` übernommen, weil der Rückschrieb von `Uid` und Label in die Dateien dazugehört.
- Das Token der Vorschau ist zustandslos: SHA-256 über Projekt, Richtung und den Plan (Schlüssel, Aktion, Hashes beider Seiten). Ändert sich etwas zwischen Vorschau und Ausführen, folgt `sync_preview_stale`.
- Auto-Sync: ein Termin `core.sync` im `Scheduler`, alle `AUTO_SYNC_INTERVAL` Sekunden (Standard 30), nur solange mindestens ein Projekt Auto-Sync an hat; `MirrorProjects` (Port, später von `workspace` erfüllt) liefert die Projekte und ihre Ordner. Bis `STORY-068` verdrahtet die Composition Root eine leere Implementierung.

### Decided

1. **Domain (reine Funktionen, Tabellentests zuerst)**: `MirrorEntry`, Plan aus beiden Seiten und dem Basis-Stand (alle Fälle aus §7.3, Richtung), Auflösung der Konflikte durch Entscheidungen, Token, Status.
2. **Ports und Zustand**: `MirrorCodec`, `SyncParticipant`, `MirrorBinding`, `MirrorProjects`, `SyncStateStore` (Adapter auf `core_sync_state`), `Ids`; `MirrorFormatError`.
3. **SyncService.status und preview**: lesen, dekodieren, normalisieren, Plan; Ordnerzustand und Formatfehler als `paused` bzw. Fehler.
4. **SyncService.execute**: Reihenfolge wie oben, mit Fake-Ports; Platzhalter und Label-Vergabe; Richtungsbeschränkung.
5. **Auto-Sync und Ereignisse**: `auto`, Termin im Scheduler, `core.sync.state`.
6. **Operationen**: `sync_status`, `sync_preview`, `sync_execute` des Core (HTTP + MCP); Verdrahtung in der Composition Root (`PluginHost` sammelt die Spiegel).
7. **Integration**: Test-Plugin (Codec + Teilnehmer auf einer echten SQLite-Tabelle) mit temporärem Ordner, Auto-Sync mit fester Uhr, `scripts/check-next.sh` grün, Techdoku.

### Open

- Keine.

## 2026-10-16 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant, mit diesen Ergänzungen: Einträge, die einen Platzhalter ersetzen, tragen im `upserts` von `encode` ihren `placeholder` (damit der Codec Zeile, Ordner und Dokumente umbenennen kann); der `SyncService` bekommt die Spiegel über eine Funktion (die Plugin-Dienste entstehen erst nach ihm); die Operationen des Core hängen an einem `CoreServices`-Objekt (UI-Zustand + Sync). `PluginHost.mirrors` liefert die Spiegel in Ladereihenfolge.
- `tests/helpers/server/mirror_plugin/` ist ein vollständiges Beispiel (Codec, Teilnehmer, Tabellen mit Label-Historie und -Zählern, Verweise über `uid`); die Plugin-Stories können es als Vorlage für ihre Teilnehmer nehmen. Fakes für Unit-Tests: `tests/helpers/server/sync_fakes.py`.
- Im Auto-Sync läuft der Takt-Callback blockierend in der Ereignisschleife; ein Lauf dauert Millisekunden. Falls das bei großen Projekten stört, wandert er später in einen Thread (die Sperre je Projekt ist schon da).

### Decided

- Abschlusskriterien geprüft: (1) Vorschau, Ausführen mit Entscheidungen, Richtungsbeschränkung und Konflikterkennung mit einem Test-Plugin (`test_sync_service.py` gegen Fakes, `test_sync_flow.py` mit echter SQLite-Datei, echtem Ordner und HTTP); (2) Einträge ohne `uid` bekommen `uid` und Label, Platzhalter in Verweisen werden umgeschrieben (auch in bestehenden Einträgen), die Dateien werden zurückgeschrieben; (3) Auto-Sync überträgt nur konfliktfreie Änderungen, löscht nie, pausiert bei Merge-Markern/Git-Lock/fehlendem Ordner/Formatfehlern, sichert vorher die Datenbank, läuft als einzelner Termin nur bei aktivem Projekt; (4) `status` ändert nichts (Test vergleicht Dateien, Basis und Datenbank vorher/nachher) und `core.sync.state` kommt als öffentliches Ereignis; (5) Formatfehler des Codecs stoppen den Sync mit Datei und Zeile (422).
- Dazu: eine fehlschlagende Teilnehmer-Änderung rollt die gesamte Datenbank-Transaktion (auch die Label-Zähler) zurück und lässt die Dateien unberührt; ein veraltetes Token wird mit 409 abgewiesen.
- `scripts/check-next.sh` grün (251 Tests); `scripts/check.sh` des alten Viewers grün.
- Status: `Awaiting confirmation`.

### Open

- Fragen 17 und 18 in `STORY-060` (Annahmen gelten).
