# TASK-013 — Note zu Task, Story oder Epic befördern (Backend)

## 2026-10-08 — Umsetzung Beförderung (Backend)

### Discussed

- Entscheidung promote aus TASK-010 braucht die Item-Felder, die der Entscheidungs-Endpunkt nicht kennt.

### Decided

- Neue Route POST /api/v2/notes/{project}/{label}/promote, Body {version, item_type, title?, summary?, area, goal, completion_criteria, parent?, required_for_parent?, priority?, dependencies?}, Antwort {note, item}.
- Entscheidung promote: POST /api/v2/notices/{id}/decision nimmt zusätzlich promotion (Item-Felder); die Note wird zuerst befördert, dann die Hinweis-Entscheidung gesetzt; Antwort enthält zusätzlich item. Ohne promotion bleibt decision_not_available (409). NoteService.decide(promote) wird nur für eine bereits beförderte Note ausgeführt.
- Neue Fehlercodes (409): promote_origin_missing (origin-Link zeigt auf ein nicht mehr vorhandenes Item), demote_document_name (siehe TASK-014).
- Ablauf: Item anlegen, sofort Link origin, Langtext und Notizen der Note als ein datierter Eintrag 'Aus Note <LABEL> befördert' in <ITEM>_notes.md (eine Zeile pro Aufzählungspunkt), Specs als <ITEM>_spec[_topic].md, dann Note finish(promoted). Wiederholung mit gleicher Version ist idempotent (Marker im Notizen-Eintrag, vorhandene Dokumente werden nicht überschrieben).
- Restfenster: scheitert das Setzen des Links origin direkt nach dem Anlegen des Items, gibt es keinen Beleg; die Wiederholung würde ein zweites Item anlegen. Bewusst nicht mit Rollback gelöst.
- Hinweise für Techdocs (STORY-046): neuer Service ConversionService (application/services/conversion.py), domain/conversion.py, ConversionRefusedError.
