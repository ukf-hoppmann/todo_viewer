import { useState } from "react";
import type { EditableField as FieldName } from "../api/client";
import { useEditItem } from "../api/queries";
import { editValue, type Item, needsResolution } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { usePausePolling } from "../state/pollingPause";
import { ResolutionDialog } from "./ResolutionDialog";

interface EditableFieldProps {
  item: Item;
  field: FieldName;
  ariaLabel: string;
  options: string[];
  label: (value: string) => string;
}

/** A select that saves on change; Completed/Rejected first ask for a resolution. */
export function EditableField({ item, field, ariaLabel, options, label }: EditableFieldProps) {
  const i18n = useI18n();
  const edit = useEditItem();
  const [focused, setFocused] = useState(false);
  const [pendingStatus, setPendingStatus] = useState<string | null>(null);
  usePausePolling(focused || edit.isPending);

  const current = editValue(item, field);

  const save = (value: string, resolution: string | null) =>
    edit.mutate({ ref: item.ref, field, value, resolution });

  const onChange = (value: string) => {
    if (!value || value === current) return;
    edit.reset();
    if (field === "status" && needsResolution(item, value)) setPendingStatus(value);
    else save(value, null);
  };

  return (
    <>
      <select
        className="field-edit"
        aria-label={ariaLabel}
        value={current}
        disabled={edit.isPending}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onChange={(e) => onChange(e.target.value)}
      >
        {!current && <option value="">—</option>}
        {options.map((o) => (
          <option key={o} value={o}>
            {label(o)}
          </option>
        ))}
      </select>
      {edit.isPending && <span className="field-status">{i18n.t("saving")}</span>}
      {edit.error && <div className="field-error">{i18n.t("err.save", { e: describeError(i18n, edit.error) })}</div>}
      {pendingStatus && (
        <ResolutionDialog
          item={item}
          status={pendingStatus}
          onCancel={() => setPendingStatus(null)}
          onConfirm={(resolution) => {
            setPendingStatus(null);
            save(pendingStatus, resolution);
          }}
        />
      )}
    </>
  );
}
