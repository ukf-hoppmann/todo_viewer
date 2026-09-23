import { useState } from "react";
import { defaultResolution, type Item } from "../domain/model";
import { useI18n } from "../i18n/i18n";
import { Modal } from "./Modal";

interface ResolutionDialogProps {
  item: Item;
  status: string;
  onConfirm: (resolution: string) => void;
  onCancel: () => void;
}

/** Asks for the resolution Completed/Rejected needs; Cmd/Ctrl+Enter saves. */
export function ResolutionDialog({ item, status, onConfirm, onCancel }: ResolutionDialogProps) {
  const { t, vocab } = useI18n();
  const [text, setText] = useState(() => defaultResolution(status));
  const [error, setError] = useState("");

  const submit = () => {
    const value = text.trim();
    if (!value) {
      setError(t("err.resolution_required"));
      return;
    }
    onConfirm(value);
  };

  return (
    <Modal labelledBy="resolution-title" onDismiss={onCancel}>
      <h3 id="resolution-title">{t("resolution.title", { status: vocab("status", status), id: item.ref.id })}</h3>
      <div>
        <label className="field" htmlFor="resolution-text">
          {t("resolution.label")}
        </label>
        <textarea
          id="resolution-text"
          autoFocus
          value={text}
          onFocus={(e) => e.currentTarget.select()}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.metaKey || e.ctrlKey) && submit()}
        />
      </div>
      {item.ref.location === "active" && <div className="hint">{t("resolution.hint")}</div>}
      <div className="modal-error">{error}</div>
      <div className="modal-actions">
        <button className="btn" onClick={onCancel}>
          {t("cancel")}
        </button>
        <button className="btn primary" onClick={submit}>
          {t("save")}
        </button>
      </div>
    </Modal>
  );
}
