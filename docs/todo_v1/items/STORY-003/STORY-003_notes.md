# STORY-003 — Notizen

## 2026-09-28 — Entwurf und Entscheidungen

### Discussed

- Die Geschäftslogik fragt nur nach „Item X aus Quelle Y“; wie das Item
  gefunden wird (Markdown-Block, später Datenbankzeile), entscheidet allein
  der Adapter in `infrastructure`.
- Checklisten (`- [ ]`) haben keine echte ID; der Viewer bildete sie bisher
  aus Dateiname und Zeile.
- Optionales oder verpflichtendes Versions-Token beim Bearbeiten.

### Decided

- Checklisten-Format wird entfernt. Nur Einträge mit klarer ID werden
  unterstützt, weil eine Datenbank sie ohnehin braucht. Ein `TODO.md` ohne
  Backlog-Format-Kennung wird als Quellenproblem gemeldet.
- Versions-Token ist beim Bearbeiten Pflicht. Es ist ein Hash über die Felder
  des Items, im Domain berechnet, also speicherunabhängig.
- `POST /api/v2/items/edit` entfällt ohne Übergangsfrist; neu sind
  `GET` und `PATCH /api/v2/items/{source_id}/{id}`.
- `ItemOut` enthält `source_id`, `id`, `archived` und `version` statt `ref`;
  `key` ist `source_id/id`. `format` entfällt.
- Neue Fehlercodes: `item_not_found` (404), `version_conflict` (409),
  `duplicate_item` (409). `entry_moved` und `checkbox_status_only` entfallen.
- `notes`/`spec` bleiben vorerst Dateipfade; `STORY-009` baut sie um.

## 2026-09-28 — Umsetzung abgeschlossen

### Discussed

- Die Version hing zunächst auch am Projektnamen der Quelle; ein Umbenennen
  der Quelle hätte alle Versionen geändert.

### Decided

- Die Version umfasst nur den gespeicherten Inhalt des Items, nicht den
  Projektnamen aus der Konfiguration.
- Die Version wird zweimal geprüft: im Service gegen die übergebene Version
  und im Markdown-Adapter erneut unter Lock direkt vor dem Schreiben.
- Änderungen an anderen Items derselben Datei (z. B. verschobene Zeilen)
  führen nicht zu einem Konflikt.

### Open

- Die Auswahlfelder der UI ließen sich im Browser-Pane nicht bedienen; der
  UI-Weg ist durch Komponententests abgedeckt, der Ablauf gegen den
  laufenden Server per `curl` geprüft. Eine manuelle Bedienprobe in der UI
  steht noch aus.
