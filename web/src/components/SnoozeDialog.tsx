import { useMemo, useState } from "react";
import { useSnoozeNote } from "../api/queries";
import type { Item } from "../domain/model";
import { snoozePresets, toIsoWithZone, toLocalInput } from "../domain/notes";
import { describeError, useI18n } from "../i18n/i18n";
import type { MessageKey } from "../i18n/messages";
import { EventTriggerFields, eventTrigger, useEventDraft } from "./EventTriggerFields";
import { Modal } from "./Modal";

interface SnoozeDialogProps {
  project: string;
  label: string;
  /** The version of the note the choice is based on. */
  version: string;
  projects: readonly string[];
  items: readonly Item[];
  onClose: () => void;
  /** Called after the note was snoozed. */
  onDone?: () => void;
}

/** Back to waiting: a quick choice (tomorrow, in a week, in 30 days), an own date, or until an event happens. */
export function SnoozeDialog({ project, label, version, projects, items, onClose, onDone }: SnoozeDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const snooze = useSnoozeNote();
  const presets = useMemo(() => snoozePresets(new Date()), []);
  const [custom, setCustom] = useState(toLocalInput(presets[0]?.at.toISOString() ?? null));
  const [withEvent, setWithEvent] = useState(false);
  const [event, setEvent] = useEventDraft(project);

  const done = () => {
    onDone?.();
    onClose();
  };
  const send = (body: { review_at?: string; trigger?: NonNullable<ReturnType<typeof eventTrigger>> }) =>
    snooze.mutate({ project, label, version, ...body }, { onSuccess: done });
  const customIso = toIsoWithZone(custom);
  const trigger = eventTrigger(event);

  return (
    <Modal labelledBy="snooze-title" onDismiss={onClose}>
      <h3 id="snooze-title">{t("snooze.title")}</h3>
      <div className="snooze-presets">
        {presets.map((preset) => (
          <button key={preset.key} className="btn" disabled={snooze.isPending} onClick={() => send({ review_at: preset.at.toISOString() })}>
            {t(`snooze.${preset.key}` as MessageKey)}
          </button>
        ))}
      </div>
      <div className="snooze-custom">
        <label className="field">
          {t("snooze.custom")}
          <input type="datetime-local" value={custom} onChange={(e) => setCustom(e.target.value)} />
        </label>
        <button className="btn" disabled={snooze.isPending || customIso === null} onClick={() => customIso && send({ review_at: customIso })}>
          {t("snooze.submit")}
        </button>
      </div>
      <label className="snooze-event-toggle">
        <input type="checkbox" checked={withEvent} onChange={(e) => setWithEvent(e.target.checked)} />
        {t("snooze.onEvent")}
      </label>
      {withEvent && (
        <div className="edit-form">
          <EventTriggerFields projects={projects} items={items} draft={event} onChange={setEvent} />
          <button className="btn" disabled={snooze.isPending || trigger === null} onClick={() => trigger && send({ trigger })}>
            {t("snooze.submitEvent")}
          </button>
        </div>
      )}
      {snooze.error && (
        <div className="field-error" role="alert">
          {t("err.save", { e: describeError(i18n, snooze.error) })}
        </div>
      )}
      <div className="modal-actions">
        <button className="btn" onClick={onClose}>
          {t("cancel")}
        </button>
      </div>
    </Modal>
  );
}
