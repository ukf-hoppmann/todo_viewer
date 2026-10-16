# STORY-067 — Gemeinsame UI-Bausteine für alle Plugins

## 2026-10-16 — Entscheidungen

### Decided

- Größeres Augenmerk auf Wiederverwendbarkeit: neue Plugins stecken Bausteine zusammen, statt sie neu zu bauen.
- Behalten aus dem alten Viewer: Baum, Abhängigkeiten, Notes, Papierkorb.
# STORY-067 — Gemeinsame UI-Bausteine für alle Plugins

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- `shared` darf nur Pakete von Dritten importieren (Scope client §1), also weder Core-Modals noch i18n-Ressourcen des Core. `ConfirmDialog` und `ChoiceDialog` sind deshalb schlichte MUI-Dialoge mit Texten als Eigenschaften (die Plugins übersetzen), nicht Aufrufe der Core-Modals. Siehe Frage 21 in `STORY-060`. Aus demselben Grund tragen alle Bausteine ihre Texte als Eigenschaften (`labels`); Standardtexte sind englisch.
- Test-IDs: Besitzer `shared`, Form `shared.<element>`, als Konstante `sharedTestIds` aus `client/src/shared/index.ts`.
- Reine Logik (flache Liste → Baum, sichtbare Knoten, Ablageposition, Überschriften, Markdown → sauberes HTML) liegt in eigenen Dateien ohne React und hat eigene Tests.
- `marked` (^18) und `dompurify` (^3) sind im Scope freigegeben und jetzt in `client/package.json`.

### Decided

1. **Logik**: `buildTree`, `flattenVisible`, `dropPosition`, `extractHeadings`, `renderMarkdown` (sauber, mit Überschrift-IDs). Tests zuerst.
2. **TreeView** (Auswahl, Tastatur, Hover-Aktionen, Drag & Drop mit `canDrop`/`onDrop`), **ProgressRing**.
3. **DetailPanel** (Kopfleiste, einklappbare Abschnitte, Felder), **InlineField**, **EditForm** mit Versionskonflikt.
4. **MarkdownView/MarkdownEditor**, **LargeView**.
5. **FilterSection**, **ConfirmDialog/ChoiceDialog**, **EntityPicker**.
6. **Beispielseite** im Test-Plugin `example`: Baum, Detailpanel und Editor zusammen.
7. **Integration**: `check-next.sh` grün, Techdoku `neubau-client.md`.

### Open

- Frage 21 in `STORY-060`.
