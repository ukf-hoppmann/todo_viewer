# STORY-077 — Notes und Topics

## 2026-10-17 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Zuschnitt.** Neues Plugin `notes` (Server und Client), das nur `workspace` braucht. Element-Typen `note` (Präfix `NOTE`) und `topic` (Präfix `TOPIC`); Titel im Register ist die Kurzfassung bzw. der Name. Auslöser, Hinweise, Befördern (STORY-078), Spiegel (STORY-079) und Wecker (STORY-080) sind nicht Teil dieser Story; das Modell lässt Platz dafür (`trigger_mode` ist schon da).
- **Tabellen** wie in der Spec (`notes_statuses`, `notes_topics`, `notes_notes`, `notes_documents`, `notes_settings`). Gespeichert werden `waiting`, `snoozed`, `done`, `dropped`, `promoted`; `due` ist abgeleitet (Prüfdatum erreicht), steht aber als feste Zeile in `notes_statuses`. `archived` an der Note heißt „im Archiv“: erledigte, verworfene und beförderte Notes immer; offene Notes, solange ihr Topic archiviert ist („parent archived“). Beim Reaktivieren werden genau die archivierten Notes im Teilbaum zurückgeholt, deren Status nicht abgeschlossen ist.
- **Fällig** (Domäne, rein): eine nicht archivierte, nicht gelöschte Note mit Status `waiting` oder `snoozed` ist fällig, wenn ihr Prüfdatum erreicht ist; archivierte Notes lösen nie etwas aus. Stichtag kommt aus der Uhr des Kerns. Neues Prüfdatum bei Anlegen, Textänderung, Behalten und Zurückstellen: heute + `review_days` (Standard 30).
- **Topics.** Tiefenregel in der Domäne (Standard 3, Einstellung 1–10): Anlegen und Verschieben prüfen die Tiefe des ganzen Teilbaums; Schleifen sind verboten; Topic und Parent müssen im selben Projekt sein. Löschen/Archivieren eines Topics mit Inhalt verlangt eine Wahl: archivierte Notes behalten (wandern ins neutrale Topic „Archiviert“ des Projekts, das beim ersten Bedarf entsteht und nicht löschbar ist), aktive Notes verschieben (Zieltopic oder „Ohne Topic“), beim Archivieren zusätzlich „aktive Notes mit archivieren“. Ohne Wahl liefert die Operation den Fehler `topic_has_content` mit den Zahlen (aktiv, archiviert, Unter-Topics).
- **Löschen/Papierkorb** über die allgemeinen Operationen von `workspace` (`trash.register`): Kinder eines Topics sind Unter-Topics und Notes; Wiederherstellen einer Note ist verboten, solange ihr Topic im Papierkorb liegt (`topic_in_trash`).
- **Dokumente** je Note wie in STORY-073: `<LABEL>_notes.md` (Kurzfassung Pflicht, ist immer da) und `<LABEL>_spec[_<thema>].md`, Versionsprüfung über `revision`, `append_note` mit Discussed/Decided/Open. Der Eintragsbau ist eine kleine Kopie aus dem Backlog, weil Plugins einander nicht importieren (Frage 29).
- **Operationen** (HTTP + MCP): `notes_index`, `get_note`, `create_note`, `update_note`, `keep_note`, `snooze_note`, `finish_note`, `restore_note`, `create_topic`, `update_topic`, `move_topic`, `archive_topic`, `reactivate_topic`, `delete_topic`, `count_due`, Dokumente (`list_note_documents`, `get_note_document`, `put_note_document`, `append_note_entry`), `get_notes_settings`/`update_notes_settings` (ohne MCP). Löschen/Wiederherstellen/Endgültiges Löschen einer Note über `delete_element` & Co. von `workspace`.
- **Client.** Hauptroute `notes/main` („Notes“): Baum Projekt → Topic → Note (Baustein `TreeView`, Hervorhebung der Topic-Bereiche der ersten beiden Ebenen mit gespeichertem Schalter „Erweiterte Markierung“, Zähler = Notes samt Unter-Topics, fällige zuerst, Hover-Aktionen am Topic), Filter Note-Status in der Seitenleiste, Detail mit Aktionsleiste (Bearbeiten, Erledigen, Verwerfen, Zurückstellen, Behalten, Löschen, Großansicht), Dokumente und Verknüpfungen, Dialoge für Topic (anlegen, umbenennen, Termin, verschieben, archivieren, löschen mit Auswahl), Drag & Drop (HTML5) für Notes und Topics auf Topics und Projekte, Fällig-Zähler im Slot `layout-header-sidebar.header-actions`, Einstellungsabschnitt „Notes“ in `core.settings-sections`, Neu-Typen Note und Topic in `workspace.create-types`.
- **Tests.** Server: Domäne zuerst (Fälligkeit, Statusübergänge, Tiefe, Löschen/Archivieren/Reaktivieren-Pläne), Repository gegen echte SQLite, Anwendungsfälle über HTTP (Umgebung `Env`). Client: Funktionen (Baumbau, Sortierung, Drop-Regeln), UI-Tests Baum, Aktionen, Dialoge, Drag & Drop, Zähler.

### Decided

1. **Server**: Domäne und Tests → Migration/Repositories → Dienste und Operationen → Einbindung in `PLUGINS`.
2. **Client**: API und reine Funktionen → Baum und Seite → Detail/Dialoge → Drag & Drop → Zähler und Einstellungen.
3. **Abschluss**: Techdoku, `check-next.sh`, `check.sh`, Status.

### Open

- Frage 29 (Dokument-Bausteine zwischen Plugins) und Frage 30 (Wiederherstellen aus dem Papierkorb) stehen in `STORY-060`.
