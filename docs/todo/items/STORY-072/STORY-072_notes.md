# STORY-072 — Backlog bearbeiten

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Regeln** (Domäne, Vorlage `src_old/backend/todo_viewer/domain/lifecycle.py`, `editing.py`, `creation.py`, `retype.py`) auf `uid` umgestellt: Lebenszyklus (Epic braucht ein Pflichtkind, bevor es `Open` verlässt; Pflichtkinder müssen weit genug sein; geschlossenes Item mit aktiven Kindern; aktives Kind unter geschlossenem Parent → `parent_closed` mit den zu öffnenden Vorfahren), Struktur (Epic ohne Parent, Parent braucht `required_for_parent`, unbekannte Verweise, Parent- und Abhängigkeitskreise). Eine Änderung wird nur abgewiesen, wenn sie eine Verletzung einführt oder erweitert; schon vorhandene blockieren andere Änderungen nicht. Fehlercodes wie im alten Viewer. Die Regel `summary_required_with_notes` gehört zu den Dokumenten (`STORY-073`).
- **Felder** wie im alten Viewer: Titel (ohne `**`), Priorität (feste Liste), Pflicht für Parent, Ziel, Fertigstellungskriterien, Kurzfassung (leer = entfernt), Bereich, Parent, Abhängigkeiten, Status. Texte werden getrimmt und zu einer logischen Zeile zusammengefasst (das Dateiformat speichert sie so). `Completed`/`Rejected` verlangen eine Entscheidung (`resolution_required`), ein anderer Status löscht sie.
- **Version.** Die Version eines Items ist die Revision des Registers. Jede schreibende Operation nimmt sie und erhöht sie (`version_conflict`).
- **Operationen** `create_item`, `update_item`, `retype_item`, `move_item`, `reopen_ancestors`, `list_areas` (alle auch MCP). Anlegen vergibt das Label im Register. Typwechsel (`retype_item`) nutzt `relabel` (die `uid` bleibt, das alte Label löst weiter auf) und schreibt Verweise auf das alte Label in den Texten der Items des Projekts um; die Antwort enthält den Hinweis auf Verweise außerhalb des Backlogs. `move_item(uid, version, parent, position)` hängt um und ordnet die Geschwister neu (Position ab 0); unter einen Parent verschoben, ohne `required_for_parent` zu haben, wird das Item Pflichtkind; ohne Parent verliert es den Wert. `reopen_ancestors(uid)` setzt das Item und die geschlossenen Vorfahren darüber von oben nach unten auf `In progress`.
- **Bereiche** entstehen mit dem ersten Item, das ihren Namen trägt („＋ Neuer Bereich…“ ist die Eingabe eines neuen Namens); `list_areas(project)` liefert die Namen für die Auswahl.
- **Archiv** ist ein Status und ein Filter (die Standardfilter blenden `Completed` und `Rejected` aus, `STORY-071`); es gibt keinen Umzug.
- **Ereignisse:** `backlog.item.changed` (öffentlich; `change`: `created`, `updated`, `moved`, `retyped`), `backlog.item.status_changed` (intern, für `notes`: `uid`, `label`, `project_uid`, `from`, `to`).
- **Löschen.** Eine Abhängigkeit auf ein gelöschtes Item bleibt bestehen und ist im Detailpanel als gelöscht markiert; die Regeln ignorieren Verweise auf Gelöschtes. Der Papierkorb (`STORY-070`) fragt bei Kindern nach; die alte Sperre „Item wird noch referenziert“ entfällt, weil nichts verloren geht.
- **Client:** Inline-Felder im Detailpanel (Status mit Entscheidungsdialog, Priorität, Bereich, Pflicht für Parent, Abhängigkeiten), Bearbeiten-Formular (`EditForm` aus `shared`, Versionskonflikt), Typ-Ändern-Dialog mit Hinweis auf altes und neues Label, „Kind anlegen“, Löschen (`useDeleteElement`), Wiedereröffnen-Dialog bei `parent_closed`, Neu-Typen Epic/Story/Task im Slot `workspace.create-types`, Drag & Drop im Baum (Parent und Reihenfolge, mit Regelprüfung durch den Server).

### Decided

1. **Domäne**: Lebenszyklus- und Strukturregeln, Feldprüfung, Anlegen, Textumschreiben; Tabellentests zuerst.
2. **Repository und Dienst**: Schreiben (`update`, Bereiche, Geschwister, Positionen), `EditService` mit Version, Regeln und Ereignissen; Tests gegen echte SQLite.
3. **Operationen** (HTTP + MCP) mit Integrationstests.
4. **Client, Teil 1**: Inline-Felder, Formular, Typwechsel, Löschen, Wiedereröffnen.
5. **Client, Teil 2**: Neu-Typen im Slot, „Kind anlegen“, Drag & Drop.
6. **Integration**: `check-next.sh`, `check.sh`, Techdoku.

### Open

- Keine neuen Fragen; die Dokument-Regel (`summary_required_with_notes`) kommt mit `STORY-073`.
