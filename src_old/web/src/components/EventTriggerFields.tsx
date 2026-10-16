import { useState } from "react";
import type { Schemas } from "../api/client";
import type { Item } from "../domain/model";
import { alreadyMet } from "../domain/notes";
import { useI18n } from "../i18n/i18n";
import { ItemPicker } from "./ItemPicker";

export const EVENT_STATUSES = ["In progress", "Awaiting confirmation", "Completed", "Rejected"] as const;

export interface EventDraft {
  project: string;
  target: string;
  status: string;
}

/** The state of the event fields, kept by whoever shows them (the editor or the snooze dialog). */
export function useEventDraft(project: string): [EventDraft, (next: Partial<EventDraft>) => void] {
  const [draft, setDraft] = useState<EventDraft>({ project, target: "", status: "Completed" });
  return [draft, (next) => setDraft((d) => ({ ...d, ...next }))];
}

/** The request for an event trigger, or null while no item is chosen. */
export function eventTrigger(draft: EventDraft): Schemas["TriggerIn"] | null {
  return draft.target === "" ? null : { kind: "event", target: draft.target, target_project: draft.project, target_status: draft.status };
}

interface EventTriggerFieldsProps {
  projects: readonly string[];
  items: readonly Item[];
  draft: EventDraft;
  onChange: (next: Partial<EventDraft>) => void;
}

/** An event trigger: the item to watch and the status that makes it arrive. An item that has the status already
 *  is announced before saving; the server decides in the end. */
export function EventTriggerFields({ projects, items, draft, onChange }: EventTriggerFieldsProps) {
  const { t, vocab } = useI18n();
  const [search, setSearch] = useState("");
  const chosen = items.find((i) => i.project === draft.project && i.id === draft.target);
  return (
    <>
      <ItemPicker
        projects={projects}
        items={items}
        project={draft.project}
        onProject={(project) => onChange({ project })}
        value={draft.target}
        onChange={(target) => onChange({ target })}
        search={search}
        onSearch={setSearch}
      />
      <label className="field">
        {t("trigger.status")}
        <select value={draft.status} onChange={(e) => onChange({ status: e.target.value })}>
          {EVENT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {vocab("status", s)}
            </option>
          ))}
        </select>
      </label>
      {alreadyMet(chosen, draft.status) && (
        <div className="hint warn-box" role="status">
          {t("trigger.alreadyMet")}
        </div>
      )}
    </>
  );
}
