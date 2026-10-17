# STORY-076 — Sync in der Oberfläche

## 2026-10-17 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Zuschnitt.** Alles im Client des Plugins `workspace` (die Core-Operationen `sync_status`, `sync_preview`, `sync_execute` und `update_project` gibt es): API-Teil, Abschnitt „Projekte“ in `core.settings-sections` mit Projektkarten, Sync-Dialog, Anzeigen ⚠ und ↻ in der Projektliste der Seitenleiste. Am Server kommt nur das Feld `last_sync` im Status dazu (aus `core_sync_state.synced_at`): „letzter Sync“ der Projektkarte.
- **Stand eines Projekts** aus `sync_status`: `in_sync` → „in Sync“; `primary_changed`/`mirror_changed`/`both_changed`/`conflicts` → „braucht dich“ (⚠); `paused` → „pausiert“ mit dem Grund (⚠: Ordner fehlt, Format-Fehler, Git-Vorgang …); ein Projekt ohne eingeschalteten Spiegel → „nicht gespiegelt“. ↻ steht bei Projekten mit automatischem Abgleich. Das SSE-Ereignis `core.sync.state` (und `core.reconnected`) lädt den Stand neu.
- **Projektkarte** (Einstellungen): Spiegel aus / Sync von Hand / Sync automatisch (`mirror_enabled`, `auto_sync`), Ordner (mit Ordner-Browser), Richtung, Stand, letzter Sync, eine Hauptaktion (nicht gespiegelt: „Spiegel einrichten“; sonst „Abgleichen …“, das den Sync-Dialog öffnet; bei Pause „Prüfen …“ mit dem Grund). Änderungen gehen als `update_project` (mit Version) an den Server. Die Karte nutzt die vorhandene Projektkarte (Dialog) zum Bearbeiten.
- **Sync-Dialog.** Lädt die Vorschau (`sync_preview`, Richtung wählbar), zeigt zuerst die Konflikte mit Feldvergleich (Datenbank | Dateien, nur abweichende Felder und Verweise), je Konflikt die Wahl Datenbank / Dateien / später, dazu Sammelknöpfe („Alle: Datenbank“, „Alle: Dateien“), danach die Übertragungen als Zusammenfassung. **Löschungen** (eine Seite hat den Eintrag nicht mehr) wirken nie über einen Sammelknopf: die Wahl, die löscht, trifft man einzeln und nur dann geht `delete_missing=true` mit. Nach dem Ausführen zeigt der Dialog das Ergebnis (zur Datenbank, zu den Dateien, neu angelegte Labels, offene Konflikte). Ein veraltetes Token (`sync_preview_stale`) lädt die Vorschau neu; Ordner- und Formatfehler zeigt der Dialog mit Datei und Zeile.
- **Tests.** UI-Tests gegen die gemockte API: Vorschau, Entscheidung einzeln und gesammelt (ohne Löschungen), Löschung nur einzeln mit Bestätigung des Flags, Ergebnis, veraltetes Token, Fehler, Stand und Anzeigen mit SSE-Neuladen, Karte mit Moduswechsel.

### Decided

1. **Server**: `last_sync` im Status.
2. **Client API und Stand**: Abfragen und Ausführen, Texte des Stands, Ereignis-Handler; Tests zuerst für die reinen Funktionen (Stand → Anzeige, Entscheidungen → Anfrage).
3. **Sync-Dialog** mit Feldvergleich und Entscheidungen.
4. **Einstellungen** (Projektkarten) und **Seitenleiste** (⚠, ↻).
5. **Integration**: `check-next.sh`, `check.sh`, Techdoku.

### Open

- Keine neuen Fragen.

## 2026-10-17 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant im Client des Plugins `workspace`: `sync.ts` (Stand, Entscheidungen, Feldvergleich), `SyncIndicator.tsx`, `SyncDialog.tsx`, `ProjectSettings.tsx`, API-Teil `getSyncStatus`/`getSyncPreview`/`executeSync`, Ereignis `core.sync.state`. Beschreibung in `docs/techdocs/neubau-client.md`; am Server nur `last_sync` im Status (`neubau-server.md`).
- Der Test `test_database_entries_reach_the_files_and_the_state_is_remembered` pinnt den ganzen Status; er nennt jetzt auch `last_sync` (das neue Feld, die übrigen Erwartungen sind unverändert).
- Die Karte benutzt den Dialog der Projektkarte (`ProjectCard`) zum Bearbeiten, statt Ordner und Richtung ein zweites Mal als Felder zu bauen.

### Decided

- Abschlusskriterien geprüft: (1) Projektkarte mit Modus (Aus / von Hand / automatisch), Ordner, Richtung, letztem Sync und einer Hauptaktion (`ProjectSettings.test.tsx`); (2) Sync-Dialog mit Vorschau, Konflikten zuerst mit Feldvergleich, einzelnen und gesammelten Entscheidungen, Löschungen nur einzeln mit `delete_missing` (`SyncDialog.test.tsx`, `sync.test.ts`); (3) Stand und ⚠/↻ in der Seitenleiste, Neuladen über `core.sync.state` (Handler im Plugin-Test, Anzeigen in `ProjectSettings.test.tsx`); (4) Tests grün.
- `scripts/check-next.sh` und `scripts/check.sh` grün. Status: `Awaiting confirmation`.

### Open

- Nicht geprüft: das echte Zusammenspiel im Browser mit laufendem Server und SSE (die Tests ersetzen die API und prüfen den Handler einzeln).
