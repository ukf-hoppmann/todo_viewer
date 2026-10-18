# TASK-017 — Nicht erreichbare Projekte: Link markieren und Hinweis erzeugen

## 2026-10-08 — Umsetzung

### Discussed

- Die Spec nennt eine Methode due_all; sie existiert nicht. Gemeint ist die Fällig-Liste: NoteService.due(project).
- Ein Lesefehler lässt sich vom fehlenden Item unterscheiden: Backlog.find wirft bei Quellenproblemen InvalidSourceError, bei fehlendem Item ItemNotFoundError.

### Decided

- Neu: reachability_of(project_registered, read_ok) und Reachability(reachable, reason) in domain/notes.py; reason ist project_not_registered oder source_unreadable (keine Pfade, keine Fehlertexte).
- NoteService.link_infos(project, label) -> list[LinkInfo] liefert Links mit Erreichbarkeit; NoteService.show und NoteService.due prüfen vorab; NoteView.reachability enthält die Item-Ziele. links_of bleibt unverändert und prüft nichts. Index und Zähler prüfen nicht: NoteService.due(project, check_links=False) für den Zähler.
- API: GET /projects/{p}/notes/{label}/links und DELETE .../links/{id} liefern reachable und unreachable_reason je Link; NoteOut.triggers[] hat reachable (bool|null, null ohne Ziel) und unreachable_reason.
- Hinweis project_unreachable beim ersten Entdecken je Ziel. Ist für dieses Ziel schon ein Hinweis dieser Ursache da (auch ein entschiedener), kommt kein neuer: sonst würde 'keep' die Note sofort wieder fällig machen. Notes im Papierkorb oder abgeschlossen bekommen keinen Hinweis.
- Item fehlt in lesbarem Projekt: erreichbar (kein Hinweis). Topic- und Note-Links werden nicht geprüft (liegen in der zentralen Datenbank). Jeder Lesefehler wird abgefangen, geloggt und als reachable=false gemeldet.
- Kehrt das Projekt zurück: reachable=true, der Hinweis bleibt offen.

### Open

- Kosten: show und due lesen je Link-Ziel ein Backlog (pro Aufruf gecacht je Projekt/Item); bei Markdown-Zielen mit vielen Notes ggf. messen.
