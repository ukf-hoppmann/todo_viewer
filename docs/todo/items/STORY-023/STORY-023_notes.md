# STORY-023 — Sync zwischen Datenbank und Markdown (to_md / from_md)

## 2026-09-30 — Umsetzung: Entscheidungen und Abweichungen von der Spec

### Discussed

- Die Ports konnten kein ganzes Backlog schreiben (create nur aktiv, EntryRenderer ohne Resolution/Notes/Spec/Deleted/freie Felder).

### Decided

- Neuer Port BacklogRepository.write_backlog(source, items, language): Markdown rendert TODO.md/archive.md neu und lässt den Text um die Einträge stehen; Datenbank macht Upsert nach Label (uid und Dokumente bleiben).
- Neuer Port DocumentStore.delete_document, damit fehlende Einzeldokumente mit delete_missing gelöscht werden können.
- Stale-Erkennung zustandslos: Die Vorschau liefert ein token (Hash über Item- und Dokumentversionen beider Seiten), confirm=true verlangt es; sonst 409 sync_stale.
- Fehlercodes: sync_path_missing, sync_same_backend, sync_source_invalid (details.reason nennt die Ursache), sync_stale.
- language der neu angelegten Markdown-Dateien: Standard en wie bei POST /backlogs (im Plan war de vorgesehen; Konsistenz der API geht vor).
- Sperre je Projekt gilt nur zwischen Syncs; Änderungen dazwischen fängt das token ab.

### Open

- Dateien in items/<ID>/, die nicht in Notes/Spec des Items stehen, meldet die Vorschau nicht als skipped: dafür fehlt ein Port zum Auflisten. Nur als Pfad notierte, nicht lesbare oder fehlende Dokumente stehen unter skipped.
- Items und Dokumente werden nicht in einer gemeinsamen Transaktion geschrieben; bei Abbruch dazwischen hilft ein erneuter Sync.
