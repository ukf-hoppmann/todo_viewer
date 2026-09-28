import { useState } from "react";
import { ApiError } from "../api/client";
import { useDeleteItem } from "../api/queries";
import type { Item } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { Modal } from "./Modal";

interface DeleteDialogProps {
  item: Item;
  onClose: () => void;
  onDeleted: () => void;
}

/** Moves an item to the trash; if it has children, lists them and asks again before including them. */
export function DeleteDialog({ item, onClose, onDeleted }: DeleteDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const remove = useDeleteItem();
  const [children, setChildren] = useState<string | null>(null);

  const submit = (cascade: boolean) =>
    remove.mutate(
      { sourceId: item.source_id, id: item.id, version: item.version, cascade },
      {
        onSuccess: onDeleted,
        onError: (e) => {
          if (e instanceof ApiError && e.code === "has_children") setChildren(e.details.items ?? "");
        },
      },
    );
  const otherError = remove.error && !(remove.error instanceof ApiError && remove.error.code === "has_children");

  return (
    <Modal labelledBy="delete-title" onDismiss={onClose}>
      <h3 id="delete-title">{t("delete.title", { id: item.id, title: item.title })}</h3>
      <p>{t("delete.text")}</p>
      {children !== null && (
        <div className="hint warn-box" role="alert">
          {t("delete.children", { items: children })}
        </div>
      )}
      {otherError && (
        <div className="field-error" role="alert">
          {describeError(i18n, remove.error)}
        </div>
      )}
      <div className="modal-actions">
        <button className="btn" onClick={onClose}>
          {t("cancel")}
        </button>
        {children === null ? (
          <button className="btn danger" disabled={remove.isPending} onClick={() => submit(false)}>
            {t("delete.confirm")}
          </button>
        ) : (
          <button className="btn danger" disabled={remove.isPending} onClick={() => submit(true)}>
            {t("delete.cascade")}
          </button>
        )}
      </div>
    </Modal>
  );
}
