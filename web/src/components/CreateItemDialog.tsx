import { useState } from "react";
import type { SourceStatus } from "../api/client";
import { useCreateItem } from "../api/queries";
import { childTypes, createRequest, newItemDraft, type NewItemDraft } from "../domain/editing";
import { type Item, PRIORITY_KEYS, type Uid, uidOf, YES_NO } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { Modal } from "./Modal";

interface CreateItemDialogProps {
  sources: SourceStatus[];
  /** Source preselected for a new item without parent. */
  sourceId: string;
  parent: Item | null;
  onClose: () => void;
  onCreated: (uid: Uid) => void;
}

/** Creates an item; with a parent it becomes its child (same backlog, fitting type). */
export function CreateItemDialog({ sources, sourceId, parent, onClose, onCreated }: CreateItemDialogProps) {
  const i18n = useI18n();
  const { t, vocab } = i18n;
  const L = (field: string) => vocab("field", field);
  const create = useCreateItem();
  const [draft, setDraft] = useState<NewItemDraft>(() => newItemDraft(sourceId, parent));
  const set = <K extends keyof NewItemDraft>(key: K, value: NewItemDraft[K]) => setDraft((d) => ({ ...d, [key]: value }));
  const usable = sources.filter((s) => !s.problem);
  const project = sources.find((s) => s.id === draft.source_id)?.project ?? "";

  const submit = () =>
    create.mutate(createRequest(draft), { onSuccess: (item) => onCreated(uidOf(item.project, item.id)) });

  return (
    <Modal labelledBy="create-title" onDismiss={onClose}>
      <form
        className="edit-form"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <h3 id="create-title">{parent ? t("create.childTitle", { id: parent.id, title: parent.title }) : t("create.title")}</h3>
        {!parent && (
          <label className="field">
            {t("create.source")}
            <select value={draft.source_id} onChange={(e) => set("source_id", e.target.value)}>
              {usable.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.project}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="field">
          {L("Type")}
          <select value={draft.type} onChange={(e) => set("type", e.target.value)}>
            {childTypes(parent).map((type) => (
              <option key={type} value={type}>
                {vocab("type", type)}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          {t("edit.titleField")}
          <input autoFocus value={draft.title} onChange={(e) => set("title", e.target.value)} />
        </label>
        <label className="field">
          {L("Area")}
          <input value={draft.area} onChange={(e) => set("area", e.target.value)} />
        </label>
        <label className="field">
          {L("Priority")}
          <select value={draft.priority} onChange={(e) => set("priority", e.target.value)}>
            {PRIORITY_KEYS.map((p) => (
              <option key={p} value={p}>
                {vocab("priority", p)}
              </option>
            ))}
          </select>
        </label>
        {parent && (
          <label className="field">
            {L("Required for parent")}
            <select value={draft.required_for_parent} onChange={(e) => set("required_for_parent", e.target.value as NewItemDraft["required_for_parent"])}>
              {YES_NO.map((v) => (
                <option key={v} value={v}>
                  {t(v === "Yes" ? "yes" : "no")}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="field">
          {L("Goal")}
          <textarea value={draft.goal} onChange={(e) => set("goal", e.target.value)} />
        </label>
        <label className="field">
          {L("Completion criteria")}
          <textarea value={draft.completion_criteria} onChange={(e) => set("completion_criteria", e.target.value)} />
        </label>
        <label className="field">
          {L("Summary")}
          <textarea value={draft.summary} onChange={(e) => set("summary", e.target.value)} />
        </label>
        {create.error && (
          <div className="field-error" role="alert">
            {t("err.save", { e: describeError(i18n, create.error) })}
          </div>
        )}
        <div className="hint">{t("create.hint", { project })}</div>
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            {t("cancel")}
          </button>
          <button type="submit" className="btn primary" disabled={create.isPending || !draft.source_id}>
            {create.isPending ? t("saving") : t("create.submit")}
          </button>
        </div>
      </form>
    </Modal>
  );
}
