import type { Schemas } from "../api/client";
import { useI18n } from "../i18n/i18n";
import { Modal } from "./Modal";

interface RetypeNoticeProps {
  result: Schemas["RetypeOut"];
  onClose: () => void;
}

/** After a type change: the new id and the server's notices (e.g. references outside the backlog). */
export function RetypeNotice({ result, onClose }: RetypeNoticeProps) {
  const { t, noticeText } = useI18n();

  return (
    <Modal labelledBy="retype-notice-title" onDismiss={onClose}>
      <h3 id="retype-notice-title">{t("retype.doneTitle", { old: result.old_id, new: result.item.id })}</h3>
      {result.notices.map((notice) => (
        <div key={notice.code} className="hint warn-box" role="note">
          {noticeText(notice.code, notice.message, notice.details)}
        </div>
      ))}
      <div className="modal-actions">
        <button className="btn primary" autoFocus onClick={onClose}>
          {t("close")}
        </button>
      </div>
    </Modal>
  );
}
