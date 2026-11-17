# MEMO-002
Uid: a687e6a8-8ba5-4c2c-8091-72f4753b0f5d
Summary: Sammelstelle für Ideen und Anforderungen zum Rewrite (EPIC-007)
Status: waiting
Topic:
Review: 2026-11-15T14:44:48.169591Z
Mode: any
Created: 2026-10-10T14:38:56.056101Z
Updated: 2026-11-17T07:15:47.801206Z
Archived: false
Deleted: 2026-11-17T07:15:47.801206Z
Links:
- reference ToDo_viewer:EPIC-007

Reine Sammelstelle, noch nicht geplant oder priorisiert. Stichwörter werden hier einsortiert, damit später klar ist, was alles zu tun ist.

## Bedienung / UI
- **Neu vereinheitlichen:** Es gibt mindestens zwei Wege, neue Elemente anzulegen (z. B. "+ Neu" oben und "+ Note" im Bereich), nicht intuitiv. Ein einheitlicher Weg für Epics, Stories, Tasks, Topics und Notes.
- **Drag & Drop:** Stories, Epics, Tasks, Topics und Notes per Drag & Drop verschieben.
- **Layout wie ezf-ui:** Header und Seitenleiste, Elemente austauschbar. Die Seitenleiste bleibt (Projekte, Status-/Prioritätsfilter).
- **Behalten:** Baum, Abhängigkeiten, Notes, Papierkorb. **Raus:** Kanban.

## Daten / Architektur
- **Plugin-Struktur in Frontend und Backend** (Vorbild EZF-Backend und ezf-ui): leerer Core als Hülle, Module bringen je eigenes Frontend und Backend mit und erweitern API, Store (Redux) usw.
- **Erste Module:** Todo und Notes.
- **Composition Root** wie in my_story_game: dort werden die Operationen zusammengesteckt.
- **MCP-Server für LLMs** neben der HTTP-API.
- **Speicher: DB relational, Markdown bleibt mit Sync (entschieden 2026-10-16).** Grund: Arbeit in der Cloud. Die Cloud-LLM arbeitet nur mit .md, lokal werden die Dateien eingesammelt und in die DB übernommen. Ziel später: Sync abschalten und nur noch lokal mit der DB arbeiten. Der Markdown-Teil muss deshalb abschaltbar sein, ohne dass der Rest etwas merkt. (Ersetzt die frühere Idee "keine Markdown-Dateien als zweite Quelle".)
- **Prioritäten (entschieden 2026-10-16):** genau 4 feste Werte, in der DB englisch, relational erzwungen; die UI zeigt sie übersetzt (DE: Dringend, Wichtig, Normal, Perspektivisch). Der Sync prüft, dass Markdown nur diese Werte enthält. Altwerte High/Medium/Low entfallen.

## Entscheidungen zum Vorgehen (2026-10-16)
- **Stack bleibt:** Python/FastAPI, React/Vite/TypeScript; im Frontend Redux Toolkit wie in ezf-ui.
- **Frontend-Core aus ezf-ui kopieren** (Plugin-Loader, Slots, Store, Prüfungen).

## Offen
- Englische Namen der 4 Prioritäten (Vorschlag: urgent, important, normal, prospective).
- Abbildung der Altwerte bei der Migration (Vorschlag: High → important, Medium → normal, Low → prospective).
- Projekte, Verknüpfungen, Ereignisse, Papierkorb: Core oder eigenes Plugin?

## Funktionen
- **Wecker-Funktion:** Eigene Funktion statt Krücke über Notes. Abgrenzung zum Backlog prüfen (Vergleich Backlog / Wecker / Notes).
