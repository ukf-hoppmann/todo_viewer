import { useState } from "react";
import { ApiError } from "../api/client";
import { fetchItem, useEditItem } from "../api/queries";
import { changedFields, dependencyCandidates, draftOf, type ItemDraft, parentCandidates, rebaseDraft } from "../domain/editing";
import { defaultResolution, type Item, needsResolution, priorityOptions, statusOptions, toItems, YES_NO } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { usePausePolling } from "../state/pollingPause";

interface ItemEditFormProps {
  item: Item;
  items: Item[];
  onDone: () => void;
}

/** Edit mode of the detail panel: nothing is saved until "Save"; a version conflict keeps the inputs. */
export function ItemEditForm({ item, items, onDone }: ItemEditFormProps) {
  const i18n = useI18n();
  const { t, vocab } = i18n;
  const L = (field: string) => vocab("field", field);
  const edit = useEditItem();
  usePausePolling(true);
  // The version the changes are based on; replaced by "load current state" after a conflict.
  const [base, setBase] = useState(item);
  const [draft, setDraft] = useState<ItemDraft>(() => draftOf(item));
  const [resolution, setResolution] = useState("");
  const set = <K extends keyof ItemDraft>(key: K, value: ItemDraft[K]) => setDraft((d) => ({ ...d, [key]: value }));

  const changes = changedFields(base, draft);
  const asksResolution = draft.status !== base.status && needsResolution(base, draft.status);
  const conflict = edit.error instanceof ApiError && edit.error.code === "version_conflict";
  const parents = parentCandidates(item, items);
  const dependencyChoices = dependencyCandidates(item, items).filter((i) => !draft.dependencies.includes(i.id));

  const onStatus = (status: string) => {
    set("status", status);
    setResolution(defaultResolution(status));
  };
  const save = () =>
    edit.mutate(
      { sourceId: base.source_id, id: base.id, version: base.version, fields: changes, resolution: asksResolution ? resolution : null },
      { onSuccess: onDone },
    );
  const reload = async () => {
    const [current] = toItems([await fetchItem(base.source_id, base.id)]);
    edit.reset();
    setDraft((d) => rebaseDraft(base, current!, d));
    setBase(current!);
  };

  return (
    <form
      className="edit-form"
      aria-label={t("edit.title")}
      onSubmit={(e) => {
        e.preventDefault();
        save();
      }}
    >
      <label className="field">
        {t("edit.titleField")}
        <input value={draft.title} onChange={(e) => set("title", e.target.value)} />
      </label>
      <label className="field">
        {L("Status")}
        <select value={draft.status} onChange={(e) => onStatus(e.target.value)}>
          {statusOptions(base).map((s) => (
            <option key={s} value={s}>
              {vocab("status", s)}
            </option>
          ))}
        </select>
      </label>
      {asksResolution && (
        <div className="field">
          <label className="field">
            {t("resolution.label")}
            <textarea value={resolution} onChange={(e) => setResolution(e.target.value)} />
          </label>
          {!base.archived && <span className="hint">{t("resolution.hint")}</span>}
        </div>
      )}
      <label className="field">
        {L("Priority")}
        <select value={draft.priority} onChange={(e) => set("priority", e.target.value)}>
          {!draft.priority && <option value="">—</option>}
          {priorityOptions(base).map((p) => (
            <option key={p} value={p}>
              {vocab("priority", p)}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        {L("Area")}
        <input value={draft.area} onChange={(e) => set("area", e.target.value)} />
      </label>
      {item.type !== "Epic" && (
        <label className="field">
          {L("Parent")}
          <select value={draft.parent} onChange={(e) => set("parent", e.target.value)}>
            <option value="">{t("edit.none")}</option>
            {draft.parent && !parents.some((p) => p.id === draft.parent) && <option value={draft.parent}>{draft.parent}</option>}
            {parents.map((p) => (
              <option key={p.uid} value={p.id}>{`${p.id} — ${p.title}`}</option>
            ))}
          </select>
        </label>
      )}
      {draft.parent && (
        <label className="field">
          {L("Required for parent")}
          <select value={draft.required_for_parent} onChange={(e) => set("required_for_parent", e.target.value as ItemDraft["required_for_parent"])}>
            {!draft.required_for_parent && <option value="">—</option>}
            {YES_NO.map((v) => (
              <option key={v} value={v}>
                {t(v === "Yes" ? "yes" : "no")}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="field">
        {L("Dependencies")}
        <span className="chip-list">
          {draft.dependencies.map((d) => (
            <span key={d} className="chip">
              {d}
              <button type="button" className="chip-remove" aria-label={t("edit.removeDependency", { id: d })}
                onClick={() => set("dependencies", draft.dependencies.filter((x) => x !== d))}>
                ✕
              </button>
            </span>
          ))}
        </span>
        <select aria-label={t("edit.addDependency")} value="" onChange={(e) => e.target.value && set("dependencies", [...draft.dependencies, e.target.value])}>
          <option value="">{t("edit.addDependency")}</option>
          {dependencyChoices.map((i) => (
            <option key={i.uid} value={i.id}>{`${i.id} — ${i.title}`}</option>
          ))}
        </select>
      </div>
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

      {edit.error && (
        <div className="field-error" role="alert">
          {t("err.save", { e: describeError(i18n, edit.error) })}
          {conflict && (
            <button type="button" className="btn small" onClick={reload}>
              {t("edit.reload")}
            </button>
          )}
        </div>
      )}
      <div className="modal-actions">
        <button type="button" className="btn" onClick={onDone}>
          {t("cancel")}
        </button>
        <button type="submit" className="btn primary" disabled={edit.isPending || Object.keys(changes).length === 0}>
          {edit.isPending ? t("saving") : t("save")}
        </button>
      </div>
    </form>
  );
}
