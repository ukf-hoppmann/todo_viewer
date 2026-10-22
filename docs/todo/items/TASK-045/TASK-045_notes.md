# TASK-045 — Kopf und Protokoll der Item-Notes in der Oberfläche

## State

- Goal/Status: Umgesetzt und im Browser mit den echten Daten geprüft; Client-Tests grün (eine Altlast in startApp.test, auch auf main rot); wartet auf Merge und Bestätigung.
- Next step: Merge nach main, Release, danach Bestätigung durch den Owner.
- Open:
  - Touch-Geräte ohne Hover (Tooltip nur durch langes Drücken)
- Decided:
  - Liste: Notizsymbol mit Hovertext, Kopf erst beim Hover geladen (2026-10-22)
  - Detail: Kopf oben, Protokoll eingeklappt (2026-10-22)
  - Fehlender Kopf dimmt das Symbol nur, Warnfarbe nur bei veraltetem Kopf (2026-10-22)
  - Kopf bearbeiten ist nicht Teil der Aufgabe (2026-10-22)
- References: Spec TASK-045_spec.md; Story STORY-093

State confirmed after entry 2026-10-22 — Kopf und Protokoll in der Oberfläche: Umfang und Umsetzung (49c1a39dcc03)

## 2026-10-22 — Kopf und Protokoll in der Oberfläche: Umfang und Umsetzung

### Discussed

- Plan: Kopf und Protokoll nur in der Detailansicht, Dateiknöpfe bleiben.
- Owner-Wunsch: den Kopf auch als Überblick in der Liste, aber nicht zu voll; das Protokoll nur im Detail.
- Beim Probelauf mit den echten Daten zeigten fast alle Items mit Notizen ein Warnsymbol, weil ältere Notizen noch keinen Kopf haben.

### Decided

- Liste: kleines Notizsymbol mit Hovertext (Kopf), erst beim ersten Hover geladen (Owner, 2026-10-22).
- Detail: Kopf oben, Protokoll eingeklappt, neuester Eintrag zuerst.
- Kopf missing dimmt das Symbol in der Liste nur, Warnfarbe nur bei stale, damit die Liste ruhig bleibt; im Detail markieren beide Zustände.
- Kopf ersetzen und bestätigen in der Oberfläche gehört nicht zu dieser Aufgabe.

### Open

- Touch-Geräte: Tooltip nur durch langes Drücken; ein Tipp-Auslöser wäre eine eigene Verbesserung.
