# Projekt-Backlog

Aktive Projektarbeit: offen, in Arbeit oder wartend auf eine Entscheidung des
Projektverantwortlichen. Erledigte und abgelehnte Einträge werden nach
`archive.md` verschoben; Notizen und Specs pro Eintrag liegen in `items/<ID>/`.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items

- `STORY-016` **Abgelehnte und fehlgeschlagene Requests protokollieren**
  - Type: Story.
  - Parent: None.
  - Status: Open.
  - Created: 2026-09-28.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: Wenn der Server einen Request ablehnt oder ein Fehler auftritt,
    lässt sich im Nachhinein nachvollziehen, welcher Request betroffen war
    und warum. Bisher erfährt nur der Aufrufer den Grund; das
    uvicorn-Zugriffslog zeigt nur den Statuscode.
  - Completion criteria: Jede 4xx/5xx-Antwort erzeugt eine Logzeile mit
    Methode, Pfad, Statuscode, Fehlercode und details; bei 5xx zusätzlich
    der Stacktrace; ein optionaler Logdateipfad ist per Umgebungsvariable
    einstellbar, ohne sie wird auf die Konsole geloggt; Tests decken die
    Logausgabe für einen 409-Regelverstoß und einen 500-Fehler ab;
    Konfiguration und Betrieb sind in den Techdocs beschrieben.
  - Summary: Auslöser: Der Server lehnte eine Story unter dem
    abgeschlossenen EPIC-004 mit 409 children_still_active ab; der Grund war
    nur über die Meldung des Aufrufers nachvollziehbar.

- `STORY-017` **Klare Antwort und Wiederöffnen-Angebot bei geschlossenem Parent**
  - Type: Story.
  - Parent: None.
  - Status: Open.
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
