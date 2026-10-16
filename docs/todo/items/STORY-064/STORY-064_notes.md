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
