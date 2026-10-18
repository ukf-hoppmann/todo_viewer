# TASK-012 — Hinweise an Items, wenn eine verlinkte Note verworfen oder befördert wird

## 2026-10-08 — Umsetzung Hinweise an Items

### Decided

- NoteService.finish legt bei dropped und promoted für jeden reference-Link auf ein Item einen Hinweis side=item an (Ursache note_dropped/note_promoted); done, trigger- und origin-Links sowie Links auf Topics und Notes erzeugen keinen. Fehler brechen das Verwerfen nicht ab.
- Die Abfrage am Item nutzt GET /api/v2/notices?side=item&project=<Projektname>&label=<ITEM-ID>&open=true; die Notes am Item mit Status liefert die bestehende Route GET /api/v2/projects/{project}/items/{label}/notes (in der Task-Spec als links-to genannt).
- Item-Hinweise machen eine Note nie fällig.
