# Projekt-Backlog

Aktive Projektarbeit: offen, in Arbeit oder wartend auf eine Entscheidung des
Projektverantwortlichen. Erledigte und abgelehnte Einträge werden nach
`archive.md` verschoben; Notizen und Specs pro Eintrag liegen in `items/<ID>/`.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items

- `STORY-016` **Wichtige Schritte und Fehler systematisch protokollieren**
  - Type: Story.
  - Parent: None.
  - Status: Awaiting confirmation.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Fehler lassen sich allein anhand des Logs analysieren:
    Start-Konfiguration, alle schreibenden Aktionen, abgelehnte Requests
    (4xx), Serverfehler (5xx) und bisher still geschluckte Fehler sind mit
    Kontext protokolliert. Das Log liegt außerhalb des Containers und bleibt
    beim Entfernen des Containers erhalten. Bisher gibt es im Backend kein
    Logging; nur das uvicorn-Zugriffslog zeigt Statuscodes.
  - Completion criteria: Beim Start werden Version und aktive Pfade
    (CONFIG_DIR, FRONTEND_DIR, BROWSE_START) geloggt; jede schreibende
    Aktion erzeugt eine INFO-Zeile mit Quelle, Item-ID bzw. Ziel und
    Ergebnis; jede 4xx-Antwort erzeugt eine Zeile mit Methode, Pfad,
    Statuscode, Fehlercode und details, jede 5xx zusätzlich den Stacktrace;
    still behandelte Fehler (unlesbare Quelle, defekte ui_state.json,
    OSError im Ordner-Browser) erzeugen eine WARNING; jede Zeile trägt eine
    Request-ID; Format einzeilig key=value, per grep durchsuchbar; LOG_FILE
    und LOG_LEVEL per Umgebungsvariable, ohne LOG_FILE Konsole; Rotation
    nach Größe (5 MB, 5 Dateien); docker-compose bindet ./logs als Volume
    ein, logs/ steht in .gitignore; Tests decken u. a. einen
    409-Regelverstoß, einen 500-Fehler und eine Schreibaktion ab;
    Konfiguration, Betrieb und Suche im Log sind in den Techdocs
    beschrieben.
  - Summary: Das Backend soll alle wichtigen Schritte und Fehler so
    protokollieren, dass sich Fehler allein über das Log (per grep, ohne
    vollständiges Lesen) analysieren lassen. Die Logdatei liegt in ./logs
    außerhalb des Containers.
  - Notes: `items/STORY-016/STORY-016_notes.md`.

- `STORY-017` **Klare Antwort und Wiederöffnen-Angebot bei geschlossenem Parent**
  - Type: Story.
  - Parent: None.
  - Status: Awaiting confirmation.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Wer ein aktives Kind an ein abgeschlossenes Epic oder eine
    abgeschlossene Story hängt, erfährt eindeutig, dass der Parent
    geschlossen ist und wie man ihn wieder öffnet; KI-Agenten verstehen die
    Antwort ohne Rätselraten, die UI bietet das Wiederöffnen direkt an.
  - Completion criteria: Der Server antwortet in diesem Fall mit 409
    parent_closed statt children_still_active, nennt das Kind und die zu
    öffnenden geschlossenen Vorfahren in Öffnungsreihenfolge und beschreibt
    in der Meldung den Weg zum Wiederöffnen; children_still_active bleibt
    für das Schließen eines Parents mit aktiven Kindern; der Anlegen-Dialog
    der UI fragt bei parent_closed, ob die Vorfahren wieder geöffnet werden
    sollen, und legt das Item danach an; übrige UI-Stellen zeigen die klare
    Meldung (de/en); interfaces.md beschreibt den Fehlercode und das
    Wiederöffnen per PATCH; Tests decken Domain, API und UI ab.
  - Summary: Auslöser: Der Harness bekam beim Anlegen einer Story unter dem
    abgeschlossenen EPIC-004 nur die missverständliche Meldung
    children_still_active und legte die Story ohne Parent an.
