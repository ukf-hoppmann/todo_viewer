import { useState } from "react";
import type { Schemas } from "../api/client";
import { useRetypeItem } from "../api/queries";
import { retypeTargets } from "../domain/editing";
import type { Item } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { Modal } from "./Modal";

interface RetypeDialogProps {
  item: Item;
  onClose: () => void;
  onRetyped: (result: Schemas["RetypeOut"]) => void;
}

/** Changes the type of an item. The server assigns the new id and follows the references in the backlog. */
export function RetypeDialog({ item, onClose, onRetyped }: RetypeDialogProps) {
  const i18n = useI18n();
  const { t, vocab } = i18n;
  const retype = useRetypeItem();
  const targets = retypeTargets(item);
  const [type, setType] = useState(targets[0] ?? "");

  return (
    <Modal labelledBy="retype-title" onDismiss={onClose}>
      <form
        className="edit-form"
        onSubmit={(e) => {
          e.preventDefault();
          retype.mutate({ sourceId: item.source_id, id: item.id, version: item.version, type }, { onSuccess: (result) => onRetyped(result) });
        }}
      >
        <h3 id="retype-title">{t("retype.title", { id: item.id })}</h3>
        <p>{t("retype.text")}</p>
        <label className="field">
          {t("retype.target")}
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {targets.map((target) => (
              <option key={target} value={target}>
                {vocab("type", target)}
              </option>
            ))}
          </select>
        </label>
        {retype.error && (
          <div className="field-error" role="alert">
            {describeError(i18n, retype.error)}
          </div>
        )}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            {t("cancel")}
          </button>
          <button type="submit" className="btn primary" disabled={retype.isPending || !type}>
            {retype.isPending ? t("saving") : t("retype.confirm")}
          </button>
        </div>
      </form>
    </Modal>
  );
}
