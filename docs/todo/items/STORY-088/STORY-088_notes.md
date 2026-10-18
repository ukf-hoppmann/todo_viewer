# STORY-088 — Wiederverwendbares Seitengerüst mit Sidebar und Detailspalte; Wecker zeigt sein Ziel

## 2026-10-18 — Prüfung Wecker-Ansicht und Seitengerüst

### Discussed

- Wecker: Ziel nicht anklickbar, Textbuttons überlappen bei schmaler Spalte.
- Split-Layout ist in BacklogPage und NotesPage kopiert, Papierkorb hat keine Detailspalte, nur DetailPanel ist gemeinsam.
- alarms darf ItemDetail/NoteDetail nicht importieren (Plugin-Grenzen); gemeinsame Datenstruktur mit Vererbung verworfen, weil sie Fachlogik aus den Plugins zöge.
- Fokusraub alle ~45-60 s am 2026-10-18 kam von externen Seitenaufrufen (GET / im viewer.log), nicht vom Sync oder der App.

### Decided

- ezf-ui ist nur Ideengeber; das Flag `sidebar` meint die von Plugins gefüllte linke Leiste, die Navigations-Sidebar mit Unterrouten entfällt.
- Rechte Detailspalte als leeres Gerüst per Flag `detail`, gefüllt über `usePageDetail`.
- Fremde Detailinhalte über Slot `workspace.element-detail` mit `ElementDetail`.
- Klick im Wecker öffnet nur die Detailspalte, keine Navigation.
- Aktionen als Icon-Buttons mit Tooltip.
- Umsetzung erst nach Abschluss der parallelen Session / des Umstiegs.

### Open

- Genaue `kind`-Werte für Notizen und Themen beim Umbau prüfen.
- Ob Header/Sidebar/Detail im Layout-Plugin oder im Core liegen (Vorschlag: Layout-Plugin).

## 2026-10-18 — Anlage im Neubau während des Umstiegs

### Discussed

- Am 2026-10-18 war der alte Viewer (Port 5411, /api/v2) gestoppt; backlog_api.py des Harness erreichte ihn nicht. Story und Tasks wurden daher direkt über /api/backlog im Neubau (Port 5412) angelegt.

### Decided

- Umsetzung beginnt trotzdem jetzt (Wunsch des Besitzers); um die Datenfrage kümmert sich der Besitzer im Anschluss.

### Open

- STORY-088 und TASK-036 bis TASK-039 stehen nur in der Datenbank des Neubaus. Übernimmt der Umstieg (STORY-084) die Daten noch einmal aus dem alten Viewer, gehen sie verloren und müssen neu angelegt werden.
- Der Spiegel docs/todo enthält sie noch nicht; kein Sync während der Umstellung auf Spiegel-Format Version 2.
