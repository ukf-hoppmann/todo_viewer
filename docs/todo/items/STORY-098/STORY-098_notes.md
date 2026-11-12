# STORY-098 — Note heißt Memo: Umbenennung des Eintragstyps, damit „Note“ nur noch die Item-Notiz meint

## State

- Goal/Status: 2026-11-12: Eintragstyp Note heißt Memo, Notice heißt Hint; Server, Client, Tests und Neubau-Doku sind im Worktree umgestellt und getestet, die Migration lief gegen eine Kopie der echten Datenbank. Nicht bereitgestellt, nicht gemergt.
- Next step: 2026-11-12: Name des Hinweises klären; mergen, Version veröffentlichen; Umstellung mit Backup, Neustart, Sync und Harness durch den Owner.
- Open: 2026-11-12: Name Hint oder anders; Reihenfolge der Umstellung; alte Doku des alten Viewers.
- Decided: 2026-11-12: Memo statt Note, Hint statt Notice, volle Tiefe inkl. Bestand; API-Pfade nur mit neuem Präfix; Dokumentart notes bleibt; Texte alter Items bleiben.
- References: STORY-077, STORY-078, STORY-079, docs/techdocs/interfaces.md (Zuordnung der MCP-Tools)

State confirmed after entry 2026-11-12 — Umsetzung im Worktree (Server, Client, Doku) (56b227ebaeb9)

## 2026-11-12 — Namensklärung Note / Memo / Hint

### Discussed

- Problem: Auf „leg eine Note an“ legt die KI mal einen Eintrag NOTE-001 an, mal eine <ID>_notes.md zu einem Item, manchmal beides.
- Optionen: (A) die Item-Datei umbenennen (z. B. _worklog.md), (B) den Eintragstyp umbenennen (Memo, Merker, Wiedervorlage). Zusätzlich verwechselbar: „Notices“ im Detail-Panel.
- Bestandsaufnahme: Der Typ steckt in Plugin-ID notes, Tabellen notes_* (Präfix folgt der Plugin-ID), 26 Routen /api/notes/..., Label NOTE-xxx, Mirror-Ordner notes/, Client-Plugin notes, Tests und Doku. Die Item-Notizen (notes_state, NotesHead, <ID>_notes.md) sind davon getrennt.

### Decided

- Der Eintragstyp heißt Memo (MEMO-001); Item-Notizen bleiben Notes. Wunsch des Owners: Notizen sind Zusätze, Memos sind eigene Blöcke.
- Umbenennung in voller Tiefe (Plugin-ID memos, Tabellen memos_*, Routen /api/memos/..., Mirror-Ordner memos/), damit die Verwechslung auch in API und Code entfällt.
- Auch Bestand und alte Namen werden umgestellt (NOTE-xxx → MEMO-xxx in Datenbank, Dateien und Verweisen); alte Tagesberichte bleiben als Historie.
- Notice heißt künftig Hint (UI deutsch: Hinweis), damit Note nur noch die Item-Notiz meint.
- Der Harness wird vom Owner separat umgestellt; hier entsteht eine Zuordnung alt → neu dafür.

### Open

- Ob alte API-Pfade /api/notes/... als Übergang erhalten bleiben (Empfehlung: nein, Viewer und Harness gleichzeitig umstellen).
- SemVer-Stufe der Veröffentlichung (Routen ändern sich; vermutlich 0.10.0).

## 2026-11-12 — Umsetzung im Worktree (Server, Client, Doku)

### Discussed

- Umsetzung per Skript über Plugin, Tests, Fixtures und Client; danach Handarbeit an den Stellen, an denen derselbe Begriff etwas anderes meint (Dokumentart `notes`/`_notes.md`, Item-Notizen im Backlog, MUI-Icons, deutsche Grammatik, „Knoten“).
- Migration: `PluginDefinition.former_ids` (Core) lässt das Plugin den Stand der alten ID erben. Version 1 und 2 von `memos` legen die Tabellen gleich neu an, Version 3 übernimmt eine Datenbank aus der Zeit von `notes` (Tabellen, Elementtyp, Labels, Zähler, Verlauf, UI-Zustand, Sync-Stand).
- Trockenlauf gegen eine Kopie der echten Datenbank: 24 Memos übernommen, Labels MEMO-xxx, Fremdschlüssel- und Integritätsprüfung sauber, der Sync-Stand der Memos entfällt.
- Namensüberschneidung: „Hint“ heißt im Backlog schon die weiche Warnung der Server-Antworten (`hints`, `hint:`-Zeilen). Der Hinweis zwischen Memo und Item (bisher Notice) heißt jetzt ebenfalls Hint; zu prüfen, ob ein anderer Name (z. B. Advisory) die Verwechslung vermeidet.
- Verweise `NOTE-nnn` in Texten alter Backlog-Einträge wurden nicht umgeschrieben: Es sind meist Beispiele und Beschreibungen in abgeschlossenen Stories; ein Umschreiben würde ihren Verlauf verfälschen.

### Decided

- Alte Namen im Bestand werden mitumgestellt (Datenbank, Label-Verlauf, Texte der Memos selbst); Texte fremder Plugins bleiben unverändert.
- Die API-Pfade behalten ihre Form: `/api/memos/memos/{ref}` (nur der Präfix ändert sich), damit die Zuordnung für den Harness eine reine Umbenennung bleibt.
- Die Dokumentart `notes` (`<LABEL>_notes.md`) bleibt für Items und Memos gleich.

### Open

- Name des Hinweises: Hint oder ein anderes Wort (Überschneidung mit den Hints des Backlogs).
- Reihenfolge der Umstellung: Veröffentlichung, Backup, Neustart des Containers (Migration läuft beim Start), Sync, dann Ordner `docs/todo/notes/` im Repository entfernen und Harness umstellen.
- Alte Doku des alten Viewers (README, techdocs/architecture, operations, configuration, alter Teil von interfaces) nennt Notes weiter; sie beschreibt `src_old`.
