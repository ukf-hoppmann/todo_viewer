# STORY-068 — Projekte, Suche und Element-Register (Plugin workspace)

## 2026-10-16 — Entscheidungen

### Decided

- Ein einheitlicher Weg zum Neuanlegen für alle Elementtypen.
- Die Seitenleiste bleibt (Projekte, Suche, Filter des aktiven Tabs).

## 2026-10-16 — Label-Historie

### Decided

- Neue Tabelle workspace_label_history: jedes Label, das ein Element je hatte; find_by_label löst auch frühere Labels auf (Entscheidung aus TASK-035).

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Abweichungen vom Datenmodell**, jeweils mit Grund (Frage 22 in `STORY-060`): `workspace_projects` bekommt `revision` (Architektur §3: schreibende Operationen nehmen ein Versions-Token) und `deleted_at` (ein mit Bestätigung entferntes Projekt samt Inhalt geht in den Papierkorb, die Elemente brauchen ihr Projekt weiter; ein leeres Projekt wird wirklich gelöscht). Das eingebaute Projekt „Allgemein“ ist am Namen erkennbar und kann weder umbenannt noch entfernt werden.
- **Elementtypen.** `PluginDefinition.element_kinds` wird eine Liste von `ElementKind(kind, label_prefix)`; die Prüfung der Plugin-Liste verlangt `workspace` in `requires`, wenn ein Plugin Typen anmeldet. Die Composition Root trägt die Typen aller aktiven Plugins nach dem Bau in `workspace_element_kinds` ein (vorhandene Zeilen bleiben, auch wenn ein Plugin abgeschaltet ist).
- **Register-Port.** Die Methoden bekommen die Transaktion des Aufrufers (`tx`), damit ein Plugin Element und eigene Zeilen atomar anlegt. Der öffentliche Teil (`ElementRegistry`, `Element`, `Project`, `Projects`) steht in `viewer.plugins.workspace`.
- **Ordner-Browser.** Plugins dürfen das Dateisystem nicht anfassen; deshalb bekommt der `FileStore`-Port `list_folders(path)` (Unterordner ohne versteckte, Elternordner), dazu Contract-Tests. Startordner: Einstellung `plugins.workspace.browse_start` oder Umgebung `BROWSE_START`, sonst der Home-Ordner.
- **MCP.** Einstellungen dürfen keine MCP-Tools sein (Architektur §3): `create_project`, `update_project`, `move_project`, `remove_project` haben `mcp=False`; `list_projects`, `browse_folders` und `resolve_label` sind Tools.
- **Sync-Anbindung.** `workspace` erfüllt `MirrorProjects` (Ordner und Auto-Sync je Projekt); die Composition Root reicht das an den `SyncService` und setzt den Auto-Sync-Termin neu, wenn ein Ereignis `workspace.project.changed` kommt.

### Decided

1. **Server, Domain und Migration**: Label-Regeln, Typen, Projekt-Regeln; Migration v1 mit den Tabellen und dem Projekt „Allgemein“. Tests zuerst (Label-Vergabe nie wiederverwendet, auch nach Löschen und Typwechsel).
2. **Register**: `register`, `relabel`, `get`, `find_by_label`, `bump_revision`, `mark_deleted`, `restore`, `purge` auf SQLite.
3. **Projekte und Operationen**: Anwendungsfälle, Operationen (HTTP + MCP), `MirrorProjects`, Ordner-Browser (`FileStore.list_folders`).
4. **Verdrahtung**: `element_kinds`, Typen eintragen, Sync-Anbindung, Ereignisse; Integrationstests über HTTP.
5. **Client**: Plugin `workspace` (Zustand mit Suche, Projekten, UI-Zustand), Seitenleiste mit Suche und Projektliste, Projektkarte mit Ordner-Browser, Neu-Dialog mit Slot `workspace.create-types` und Knopf „＋ Neu“.
6. **Integration**: `check-next.sh` grün, Techdoku.

### Open

- Frage 22 in `STORY-060`.
