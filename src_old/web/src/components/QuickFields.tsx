// Fields that can be changed outside the edit mode: one click, saved at once, easy to undo.
import { useState } from "react";
import { useEditItem } from "../api/queries";
import { areaOptions, dependencyCandidates, draftOf, type ItemDraft, quickChange } from "../domain/editing";
import { defaultResolution, type Item, needsResolution, priorityOptions, statusOptions, type Uid, YES_NO } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { usePausePolling } from "../state/pollingPause";
import { Modal } from "./Modal";

type QuickField = keyof ItemDraft;

export interface QuickEdit {
  save: (field: QuickField, value: ItemDraft[QuickField], resolution?: string) => void;
  pending: boolean;
  /** The error of the last direct change, shown next to its field. */
  error: (field: QuickField) => string | null;
}

/** One direct change at a time: every control is disabled while a change is being saved. */
export function useQuickEdit(item: Item): QuickEdit {
  const i18n = useI18n();
  const edit = useEditItem();
  const [failed, setFailed] = useState<{ uid: Uid; field: QuickField; message: string } | null>(null);

  const save: QuickEdit["save"] = (field, value, resolution) => {
    const fields = quickChange(item, { [field]: value });
    if (Object.keys(fields).length === 0) return;
    setFailed(null);
    edit.mutate(
      { sourceId: item.source_id, id: item.id, version: item.version, fields, resolution: resolution ?? null },
      { onError: (e) => setFailed({ uid: item.uid, field, message: describeError(i18n, e) }) },
    );
  };
  const error = (field: QuickField) => (failed && failed.uid === item.uid && failed.field === field ? failed.message : null);
  return { save, pending: edit.isPending, error };
}

function QuickError({ quick, field }: { quick: QuickEdit; field: QuickField }) {
  const { t } = useI18n();
  const message = quick.error(field);
  return message ? (
    <div className="field-error" role="alert">
      {t("err.save", { e: message })}
    </div>
  ) : null;
}

interface FieldProps {
  item: Item;
  quick: QuickEdit;
}

export function QuickStatus({ item, quick }: FieldProps) {
  const { vocab } = useI18n();
  const [asking, setAsking] = useState<string | null>(null);
  const onChange = (status: string) => (needsResolution(item, status) ? setAsking(status) : quick.save("status", status));

  return (
    <>
      <select className="field-edit" aria-label={vocab("field", "Status")} value={item.status} disabled={quick.pending}
        onChange={(e) => onChange(e.target.value)}>
        {statusOptions(item).map((s) => (
          <option key={s} value={s}>
            {vocab("status", s)}
          </option>
        ))}
      </select>
      <QuickError quick={quick} field="status" />
      {asking && (
        <ResolutionDialog
          item={item}
          status={asking}
          onCancel={() => setAsking(null)}
          onConfirm={(resolution) => {
            setAsking(null);
            quick.save("status", asking, resolution);
          }}
        />
      )}
    </>
  );
}

function ResolutionDialog({ item, status, onCancel, onConfirm }: {
  item: Item;
  status: string;
  onCancel: () => void;
  onConfirm: (resolution: string) => void;
}) {
  const { t, vocab } = useI18n();
  const [text, setText] = useState(() => defaultResolution(status));

  return (
    <Modal labelledBy="resolution-title" onDismiss={onCancel}>
      <h3 id="resolution-title">{t("resolution.title", { id: item.id, status: vocab("status", status) })}</h3>
      <label className="field">
        {t("resolution.label")}
        <textarea value={text} autoFocus onChange={(e) => setText(e.target.value)} />
      </label>
      {!item.archived && <span className="hint">{t("resolution.hint")}</span>}
      <div className="modal-actions">
        <button className="btn" onClick={onCancel}>
          {t("cancel")}
        </button>
        <button className="btn primary" disabled={!text.trim()} onClick={() => onConfirm(text.trim())}>
          {t("save")}
        </button>
      </div>
    </Modal>
  );
}

export function QuickPriority({ item, quick }: FieldProps) {
  const { vocab } = useI18n();
  const value = item.priority ?? "";
  return (
    <>
      <select className="field-edit" aria-label={vocab("field", "Priority")} value={value} disabled={quick.pending}
        onChange={(e) => quick.save("priority", e.target.value)}>
        {!value && <option value="">—</option>}
        {priorityOptions(item).map((p) => (
          <option key={p} value={p}>
            {vocab("priority", p)}
          </option>
        ))}
      </select>
      <QuickError quick={quick} field="priority" />
    </>
  );
}

export function QuickRequired({ item, quick }: FieldProps) {
  const { t, vocab } = useI18n();
  const value = draftOf(item).required_for_parent;
  return (
    <>
      <select className="field-edit" aria-label={vocab("field", "Required for parent")} value={value} disabled={quick.pending}
        onChange={(e) => quick.save("required_for_parent", e.target.value as ItemDraft["required_for_parent"])}>
        {!value && <option value="">—</option>}
        {YES_NO.map((v) => (
          <option key={v} value={v}>
            {t(v === "Yes" ? "yes" : "no")}
          </option>
        ))}
      </select>
      <QuickError quick={quick} field="required_for_parent" />
    </>
  );
}

const NEW_AREA = "\u0000new";

export function QuickArea({ item, items, quick }: FieldProps & { items: Item[] }) {
  const { t, vocab } = useI18n();
  const [adding, setAdding] = useState(false);
  const value = item.area ?? "";
  return (
    <>
      {adding ? (
        <NewAreaInput
          onCancel={() => setAdding(false)}
          onSave={(area) => {
            setAdding(false);
            quick.save("area", area);
          }}
        />
      ) : (
        <select className="field-edit" aria-label={vocab("field", "Area")} value={value} disabled={quick.pending}
          onChange={(e) => (e.target.value === NEW_AREA ? setAdding(true) : quick.save("area", e.target.value))}>
          {!value && <option value="">—</option>}
          {areaOptions(item, items).map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
          <option value={NEW_AREA}>{t("quick.newArea")}</option>
        </select>
      )}
      <QuickError quick={quick} field="area" />
    </>
  );
}

function NewAreaInput({ onSave, onCancel }: { onSave: (area: string) => void; onCancel: () => void }) {
  const { t } = useI18n();
  const [text, setText] = useState("");
  usePausePolling(true);
  return (
    <input className="field-edit" aria-label={t("quick.newAreaField")} placeholder={t("quick.newAreaField")} autoFocus
      value={text}
      onChange={(e) => setText(e.target.value)}
      onBlur={onCancel}
      onKeyDown={(e) => {
        if (e.key === "Escape") onCancel();
        if (e.key === "Enter" && text.trim()) onSave(text.trim());
      }}
    />
  );
}

export function QuickDependencies({ item, items, quick, onSelect }: FieldProps & { items: Item[]; onSelect: (uid: Uid) => void }) {
  const { t } = useI18n();
  const choices = dependencyCandidates(item, items).filter((i) => !item.dependencies.includes(i.id));
  return (
    <>
      <span className="chip-list">
        {item.dependencies.map((id, index) => {
          const uid = item.dependencyUids[index]!;
          return (
            <span key={id} className="chip">
              <button className="chip-link" onClick={() => onSelect(uid)}>
                {id}
              </button>
              <button className="chip-remove" aria-label={t("edit.removeDependency", { id })} disabled={quick.pending}
                onClick={() => quick.save("dependencies", item.dependencies.filter((d) => d !== id))}>
                ✕
              </button>
            </span>
          );
        })}
      </span>
      <select className="field-edit" aria-label={t("edit.addDependency")} value="" disabled={quick.pending}
        onChange={(e) => e.target.value && quick.save("dependencies", [...item.dependencies, e.target.value])}>
        <option value="">{t("edit.addDependency")}</option>
        {choices.map((i) => (
          <option key={i.uid} value={i.id}>{`${i.id} — ${i.title}`}</option>
        ))}
      </select>
      <QuickError quick={quick} field="dependencies" />
    </>
  );
}
