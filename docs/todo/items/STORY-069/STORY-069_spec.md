# `STORY-069` — Verknüpfungen

Grundlage: `EPIC-007_spec.md`, Abschnitt 9.

## Datenmodell

`workspace_links(uid PK, from_uid FK, to_uid FK, role CHECK in
('reference','origin','trigger'), created_at, UNIQUE(from_uid, to_uid, role))`.
Verknüpfungen zu Elementen im Papierkorb bleiben bestehen und werden markiert.

## Ports und Ereignisse

`Links`: `add`, `remove`, `outgoing(uid)`, `incoming(uid)`. Ereignis
`workspace.links.changed` (public). Eine Verknüpfung mit Rolle `trigger`
gehört zu einem Auslöser von `notes` und wird nur von dort angelegt.

## Operationen

`add_link`, `remove_link`, `list_links(uid)`.

## Frontend

Slot `workspace.detail-sections`: Abschnitt „Verknüpfungen“ mit
`EntityPicker` zum Hinzufügen; Plugins binden ihn in ihre Detailpanels ein.

## Tests

Test zuerst: Rollen, Eindeutigkeit, projektübergreifend, Typwechsel des Ziels.
