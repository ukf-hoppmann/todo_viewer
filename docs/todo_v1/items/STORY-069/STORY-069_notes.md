# STORY-069 — Verknüpfungen zwischen Elementen

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- Die Verknüpfungen gehören zum Plugin `workspace` (Migration v2, Tabelle `workspace_links`). Eine Verknüpfung hängt an den `uid`s, überlebt also Typwechsel und Umbenennen. Verknüpfungen zu Elementen im Papierkorb bleiben und werden in der Ausgabe als `deleted` markiert; wird ein Element endgültig gelöscht, gehen seine Verknüpfungen mit (Fremdschlüssel mit `ON DELETE CASCADE`).
- Der Port `Links` (`add`, `remove`, `outgoing`, `incoming`) nimmt wie das Register die Transaktion des Aufrufers. Die Rolle `trigger` darf der Port setzen (das Plugin `notes` ruft ihn); die Operationen `add_link` und `remove_link` lehnen sie ab (`trigger_link_reserved`), weil sie nur von dort angelegt und entfernt wird.
- Verknüpfungen sind unveränderlich (anlegen, entfernen), deshalb tragen sie kein Versions-Token. Eine Verknüpfung auf sich selbst und eine doppelte (`from`, `to`, `role`) werden abgewiesen (`invalid_link`, `link_exists`).
- Ereignis `workspace.links.changed` (öffentlich): `{change: "added"|"removed", uid, from_uid, to_uid, role}`.
- Client: der Abschnitt „Verknüpfungen“ ist eine Komponente `LinksSection` (Eigenschaft `elementUid`), die Plugins in ihr Detailpanel einbauen. Der Spec nach heißt der Slot `workspace.detail-sections`; ein Slot-Eintrag bekommt aber keine Eigenschaften (Plugin-Vertrag). Annahme (Frage 24): `workspace` exportiert `LinksSection` und `useElementLinks`; der Slot entfällt, solange der Vertrag keine Eigenschaften für Widgets kennt. Das Hinzufügen wählt das Ziel mit dem `EntityPicker` aus `shared`; die Kandidaten kommen aus einem Suchbefehl des Servers (`search_elements`), der über alle Projekte nach Label sucht.

### Decided

1. **Domain und Migration**: Rollen, Link, Fehler, Migration v2. Tests zuerst (Rollen, Eindeutigkeit, projektübergreifend, Typwechsel des Ziels).
2. **Port `Links`** und Speicher auf SQLite; Ereignis.
3. **Operationen** `add_link`, `remove_link`, `list_links(uid)`, `search_elements(query)` (HTTP + MCP); Integrationstests.
4. **Client**: API, `LinksSection` mit Liste (ausgehend/eingehend, gelöscht markiert), Hinzufügen und Entfernen; UI-Tests.
5. **Integration**: `check-next.sh`, `check.sh`, Techdoku.

### Open

- Frage 24 und 25 in `STORY-060`.

## 2026-10-16 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant, im Plugin `workspace` (Migration v2: Spalte `title`, Tabelle `workspace_links`). Beschreibung in `docs/techdocs/neubau-server.md` und `neubau-client.md`.
- Abweichungen von der Spec: kein Slot `workspace.detail-sections`, sondern die Komponente `LinksSection` (Frage 24); das Register bekommt einen Titel (Frage 25); zusätzliche Operation `search_elements`. Der `EntityPicker` aus `shared` hat dafür die Eigenschaft `onInputChange`.

### Decided

- Abschlusskriterien geprüft: (1) Verknüpfungen mit `reference`, `origin`, `trigger` anlegen und entfernen: API und MCP (`test_links.py`, 11 Tests; `trigger` nur über den Port, die Operationen lehnen ihn ab), UI (`LinksSection.test.tsx`); (2) Typwechsel und Umbenennen: die Verknüpfung hängt an der `uid` (`test_links_survive_a_kind_change_and_follow_the_new_label`), Papierkorb markiert, endgültiges Löschen nimmt sie mit; (3) die Detailpanels zeigen ausgehende und eingehende Verknüpfungen über `LinksSection`; (4) alle Tests grün.
- `scripts/check-next.sh` und `scripts/check.sh` grün.
- Status: `Awaiting confirmation`.

### Open

- Frage 24 und 25 in `STORY-060` (Annahmen gelten).
- Nicht geprüft: das Einbinden in ein echtes Detailpanel (kommt mit `STORY-071`); das Anlegen von `trigger`-Verknüpfungen durch Auslöser (kommt mit `STORY-078`).
