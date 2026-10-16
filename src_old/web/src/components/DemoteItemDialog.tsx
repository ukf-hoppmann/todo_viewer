import { useState } from "react";
import { useDemoteItem, useNotesIndex } from "../api/queries";
import type { Item } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { useUiState } from "../state/useUiStateStore";
import { Modal } from "./Modal";

interface DemoteItemDialogProps {
  item: Item;
  /** Called when the item went back to a note (the item is closed now); the dialog stays to offer the note. */
  onDemoted: () => void;
  onClose: () => void;
}

/** Turns an open item back into a note: says what happens, takes an optional topic, and offers the note afterwards. */
export function DemoteItemDialog({ item, onDemoted, onClose }: DemoteItemDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const { dispatch } = useUiState();
  const index = useNotesIndex(true);
  const demote = useDemoteItem();
  const [topic, setTopic] = useState("");
  const topics = (index.data?.topics ?? []).filter((x) => x.project === item.project);
  const note = demote.data?.note;

  if (note) {
    return (
      <Modal labelledBy="demote-title" onDismiss={onClose}>
        <h3 id="demote-title">{t("demote.done", { label: note.label })}</h3>
        <div className="modal-actions">
          <button className="btn" onClick={onClose}>
            {t("close")}
          </button>
          <button
            className="btn primary"
            onClick={() => {
              dispatch({ type: "openNote", note: { project: note.project, label: note.label } });
              onClose();
            }}
          >
            {t("demote.openNote")}
          </button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal labelledBy="demote-title" onDismiss={onClose}>
      <form
        className="edit-form"
        onSubmit={(e) => {
          e.preventDefault();
          demote.mutate({ sourceId: item.source_id, id: item.id, version: item.version, topic: topic || null }, { onSuccess: onDemoted });
        }}
      >
        <h3 id="demote-title">{t("demote.title", { id: item.id })}</h3>
        <p>{t("demote.text")}</p>
        {topics.length > 0 && (
          <label className="field">
            {t("demote.topic")}
            <select value={topic} onChange={(e) => setTopic(e.target.value)}>
              <option value="">{t("note.create.noTopic")}</option>
              {topics.map((x) => (
                <option key={x.label} value={x.label}>
                  {x.path.join(" › ")}
                </option>
              ))}
            </select>
          </label>
        )}
        {demote.error && (
          <div className="field-error" role="alert">
            {describeError(i18n, demote.error)}
          </div>
        )}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            {t("cancel")}
          </button>
          <button type="submit" className="btn danger" disabled={demote.isPending}>
            {demote.isPending ? t("saving") : t("demote.submit")}
          </button>
        </div>
      </form>
    </Modal>
  );
}
