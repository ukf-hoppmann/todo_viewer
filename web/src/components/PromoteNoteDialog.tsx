import { useState } from "react";
import { useDecideNotice, usePromoteNote } from "../api/queries";
import { parentCandidates, type PromoteDraft, promoteDraft, promoteFields, promoteRequest } from "../domain/conversion";
import { PRIORITY_KEYS, type Item, uidOf, YES_NO } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { useUiState } from "../state/useUiStateStore";
import { Modal } from "./Modal";

interface PromoteNoteDialogProps {
  note: { project: string; label: string; version: string; summary: string; body: string | null };
  items: readonly Item[];
  /** A change notice that this promotion decides (the due list): the decision route is used instead of the plain one. */
  notice?: { id: number };
  onClose: () => void;
}

const TYPES = ["Epic", "Story", "Task"] as const;

/** Turns a note into an Epic, Story or Task of its project. Title, summary and goal start from the note.
 *  After success the dialog says which item it became and offers to open it. */
export function PromoteNoteDialog({ note, items, notice, onClose }: PromoteNoteDialogProps) {
  const i18n = useI18n();
  const { t, vocab } = i18n;
  const L = (field: string) => vocab("field", field);
  const { dispatch } = useUiState();
  const promote = usePromoteNote();
  const decide = useDecideNotice();
  const mutation = notice ? decide : promote;
  const [draft, setDraft] = useState<PromoteDraft>(() => promoteDraft(note));
  const set = <K extends keyof PromoteDraft>(key: K, value: PromoteDraft[K]) => setDraft((d) => ({ ...d, [key]: value }));
  const parents = parentCandidates(items, note.project, draft.item_type);
  const created = notice ? decide.data?.item : promote.data?.item;

  if (created) {
    return (
      <Modal labelledBy="promote-title" onDismiss={onClose}>
        <h3 id="promote-title">{t("promote.done", { id: created.id })}</h3>
        <div className="modal-actions">
          <button className="btn" onClick={onClose}>
            {t("close")}
          </button>
          <button
            className="btn primary"
            onClick={() => {
              dispatch({ type: "view", view: "tree" });
              dispatch({ type: "select", uid: uidOf(created.project, created.id) });
              onClose();
            }}
          >
            {t("promote.openItem")}
          </button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal labelledBy="promote-title" onDismiss={onClose}>
      <form
        className="edit-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (notice) decide.mutate({ id: notice.id, decision: "promote", version: note.version, promotion: promoteFields(draft) });
          else promote.mutate({ project: note.project, label: note.label, ...promoteRequest(draft, note.version) });
        }}
      >
        <h3 id="promote-title">{t("promote.title", { label: note.label })}</h3>
        <label className="field">
          {t("promote.type")}
          <select
            value={draft.item_type}
            onChange={(e) => setDraft((d) => ({ ...d, item_type: e.target.value as PromoteDraft["item_type"], parent: "", required_for_parent: "" }))}
          >
            {TYPES.map((type) => (
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
        {parents.length > 0 && (
          <label className="field">
            {t("promote.parent")}
            <select
              value={draft.parent}
              onChange={(e) => setDraft((d) => ({ ...d, parent: e.target.value, required_for_parent: e.target.value ? "Yes" : "" }))}
            >
              <option value="">{t("promote.noParent")}</option>
              {parents.map((p) => (
                <option key={p.id} value={p.id}>
                  {`${p.id} — ${p.title}`}
                </option>
              ))}
            </select>
          </label>
        )}
        {draft.parent && (
          <label className="field">
            {L("Required for parent")}
            <select value={draft.required_for_parent} onChange={(e) => set("required_for_parent", e.target.value as PromoteDraft["required_for_parent"])}>
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
        <div className="hint">{t("promote.hint")}</div>
        {mutation.error && (
          <div className="field-error" role="alert">
            {t("err.save", { e: describeError(i18n, mutation.error) })}
          </div>
        )}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            {t("cancel")}
          </button>
          <button type="submit" className="btn primary" disabled={mutation.isPending}>
            {mutation.isPending ? t("saving") : t("promote.submit")}
          </button>
        </div>
      </form>
    </Modal>
  );
}
