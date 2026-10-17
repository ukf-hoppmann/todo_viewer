# STORY-064 — Infrastruktur Dateien: atomares Schreiben, Konflikte, Merge-Marker

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- Vorlagen im Altcode: `text_file.py` (atomares Schreiben, Zeilenenden), `merge_markers.py` (Marker am Zeilenanfang), `notes_files/mirror.py`. Sie werden angepasst kopiert, nichts wird importiert.
- Die reine Logik (Version = SHA-256, Zeilenenden, Marker-Erkennung, Pfadprüfung) liegt in `core/domain/files.py` und ist ohne Dateisystem testbar. Das Dateisystem kennt nur der Adapter.
- Der Sync (`STORY-065`) will gegen einen In-Memory-Ersatz testen. Dafür entsteht schon hier ein Fake `InMemoryFileStore` unter `tests/helpers/server/`, und die Contract-Suite läuft gegen beide Adapter, damit der Fake dem echten Verhalten entspricht.
- `inspect(folder)` bekommt einen Parameter `patterns` (Standard `**/*.md`): Ohne ihn weiß der Adapter nicht, welche Dateien er auf Marker prüfen soll. Siehe Frage 16 in `STORY-060`.

### Decided

1. **Domain**: Datentypen `FileEntry`, `FileSet`, `WriteFile`/`RenameFile`/`DeleteFile`, `FolderState`; Fehler `MirrorConflict` (`mirror_conflict`) und `MirrorBlocked` (`mirror_blocked`); reine Funktionen für Version, Zeilenenden, Marker, Pfadprüfung. Tests zuerst.
2. **Port und Adapter lesen**: `FileStore.read` und `inspect`; `LocalFileStore` liest nach Mustern, UTF-8 streng, meldet fehlenden Ordner, unlesbare Dateien, Merge-Marker und `.git/*.lock`, statt zu lesen.
3. **Adapter schreiben**: `write` prüft alle erwarteten Versionen vor der ersten Änderung (`mirror_conflict`), schreibt atomar (temporäre Datei + `os.replace`), behält CRLF/LF und Dateirechte, macht bei einem Fehler mitten im Lauf die schon angewendeten Änderungen rückgängig.
4. **Fake und Contract-Suite**: `InMemoryFileStore`; `test_file_store.py` als Contract-Suite für beide Adapter.
5. **Integration**: `scripts/check-next.sh` grün, Techdoku.

### Open

- Keine.

## 2026-10-16 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant. Das Verhalten ist durch die Contract-Suite `tests/implementation/integration/server/contract/test_file_store.py` festgelegt, die gegen `LocalFileStore` (echte temporäre Ordner) und gegen den Fake `InMemoryFileStore` läuft; `test_local_file_store.py` prüft nur Dateisystem-Eigenschaften (Dateirechte, Worktree-`.git`, Git-Lock im übergeordneten Repository, parallele Schreiber).
- `write` verlangt für jeden berührten Pfad eine erwartete Version (sonst `ValueError`, ein Programmierfehler) und macht bei einem Fehler mitten im Lauf alle berührten Dateien rückgängig. Das ist mehr als „soweit das Dateisystem es zulässt“ und kostet nur einen Lesevorgang vorab.
- Zeilenenden: gemischte Dateien gelten als CRLF, wenn es mehr CRLF- als LF-Zeilen gibt.

### Decided

- Abschlusskriterien geprüft: (1) Ordner als Menge von Dateien mit Inhalt und SHA-256-Version gelesen; (2) Schreiben atomar (keine temporären Dateien übrig, Rollback bei Fehler) und LF/CRLF erhalten; (3) geänderte, neu entstandene oder verschwundene Dateien führen zu `mirror_conflict`, ohne etwas zu ändern; (4) Merge-Marker, `.git/*.lock` (auch Worktree und übergeordnetes Repository), unlesbare Dateien und fehlender Ordner werden als `mirror_blocked` gemeldet, statt zu lesen; (5) Contract-Tests gegen echte temporäre Ordner grün.
- `scripts/check-next.sh` grün (176 Tests); `scripts/check.sh` des alten Viewers grün.
- Status: `Awaiting confirmation`.

### Open

- Frage 16 in `STORY-060` (Annahme gilt).
