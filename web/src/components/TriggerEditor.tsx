import { useState } from "react";
import type { Schemas } from "../api/client";
import { useAddTrigger, useRemoveTrigger } from "../api/queries";
import type { Item } from "../domain/model";
import { describeTrigger, type IndexTopic, toIsoWithZone, type TriggerInfo } from "../domain/notes";
import { describeError, useI18n } from "../i18n/i18n";
import { EventTriggerFields, eventTrigger, useEventDraft } from "./EventTriggerFields";

interface TriggerEditorProps {
  project: string;
  label: string;
  triggers: readonly TriggerInfo[];
  /** The topic of the note, if any: a topic-due trigger needs one with a due date. */
  topic: IndexTopic | undefined;
  projects: readonly string[];
  items: readonly Item[];
  /** Closed or deleted notes can be read but not changed. */
  readOnly: boolean;
}

type Kind = Schemas["TriggerIn"]["kind"];

/** The triggers of a note: shown with their state and removable; new ones of the three kinds (time, event, topic due).
 *  The mode any/all is not offered; the note keeps whatever it has. */
export function TriggerEditor({ project, label, triggers, topic, projects, items, readOnly }: TriggerEditorProps) {
  const i18n = useI18n();
  const { t, lang } = i18n;
  const add = useAddTrigger();
  const remove = useRemoveTrigger();
  const [adding, setAdding] = useState(false);
  const [kind, setKind] = useState<Kind>("time");
  const [at, setAt] = useState("");
  const [event, setEvent] = useEventDraft(project);
  const topicDue = topic?.due_at != null;

  const request = (): Schemas["TriggerIn"] | null => {
    if (kind === "time") {
      const iso = toIsoWithZone(at);
      return iso === null ? null : { kind, at: iso };
    }
    return kind === "event" ? eventTrigger(event) : topicDue ? { kind } : null;
  };
  const ready = request() !== null;
  const submit = () => {
    const body = request();
    if (body) add.mutate({ project, label, ...body }, { onSuccess: () => { setAdding(false); setAt(""); } });
  };

  return (
    <section className="note-section">
      <h3>{t("trigger.title")}</h3>
      {triggers.length === 0 && <div className="hint">{t("trigger.empty")}</div>}
      <ul className="note-links">
        {triggers.map((trigger) => {
          const text = describeTrigger(trigger, lang);
          return (
            <li key={trigger.id} className="note-link">
              <span>{t(text.key, text.params)}</span>
              <span className={`badge ${text.fired ? "note-due" : ""}`}>{text.fired ? t("trigger.fired") : t("trigger.open")}</span>
              {text.alreadyMet && <span className="hint">{t("trigger.wasMet")}</span>}
              {trigger.reachable === false && <span className="badge unreachable">{t("note.links.unreachable")}</span>}
              {!readOnly && (
                <button className="btn small" disabled={remove.isPending} onClick={() => remove.mutate({ project, label, triggerId: trigger.id })}>
                  {t("trigger.remove")}
                </button>
              )}
            </li>
          );
        })}
      </ul>
      {remove.error && (
        <div className="field-error" role="alert">
          {describeError(i18n, remove.error)}
        </div>
      )}
      {!readOnly && !adding && (
        <button className="btn small" onClick={() => setAdding(true)}>
          {t("trigger.add")}
        </button>
      )}
      {!readOnly && adding && (
        <form
          className="edit-form note-link-form"
          aria-label={t("trigger.add")}
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <label className="field">
            {t("trigger.kind")}
            <select value={kind} onChange={(e) => setKind(e.target.value as Kind)}>
              <option value="time">{t("trigger.kind.time")}</option>
              <option value="event">{t("trigger.kind.event")}</option>
              <option value="topic_due">{t("trigger.kind.topicDue")}</option>
            </select>
          </label>
          {kind === "time" && (
            <label className="field">
              {t("trigger.at")}
              <input type="datetime-local" value={at} onChange={(e) => setAt(e.target.value)} />
            </label>
          )}
          {kind === "event" && <EventTriggerFields projects={projects} items={items} draft={event} onChange={setEvent} />}
          {kind === "topic_due" && !topicDue && <div className="hint">{t("trigger.noTopicDue")}</div>}
          {add.error && (
            <div className="field-error" role="alert">
              {t("err.save", { e: describeError(i18n, add.error) })}
            </div>
          )}
          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setAdding(false)}>
              {t("cancel")}
            </button>
            <button type="submit" className="btn primary" disabled={add.isPending || !ready}>
              {add.isPending ? t("saving") : t("trigger.submit")}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
