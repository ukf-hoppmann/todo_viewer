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
