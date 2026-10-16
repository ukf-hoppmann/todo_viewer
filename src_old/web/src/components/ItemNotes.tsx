import { useAcknowledgeNotice, useItemNotices, useNotesLinkedToItem } from "../api/queries";
import { describeNotice, sortLinkedNotes } from "../domain/due";
import type { Item } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import type { MessageKey } from "../i18n/messages";
import { useUiState } from "../state/useUiStateStore";

/** At a backlog item: the notes that point at it (also those of other projects) with their status, a jump into
 *  each, and the open notices to take note of. Nothing is shown if there is neither. */
export function ItemNotes({ item }: { item: Item }) {
  const i18n = useI18n();
  const { t } = i18n;
  const { dispatch } = useUiState();
  const linked = useNotesLinkedToItem(item.project, item.id);
  const notices = useItemNotices(item.project, item.id);
  const acknowledge = useAcknowledgeNotice();
  const notes = sortLinkedNotes(linked.data ?? []);
  const open = notices.data ?? [];
  if (notes.length === 0 && open.length === 0) return null;

  return (
    <section className="detail-field item-notes">
      <div className="k">{t("itemNotes.title")}</div>
      <ul className="note-links">
        {notes.map((note) => (
          <li key={`${note.project}/${note.label}/${note.link_id}`} className="note-link">
            <button className="link-btn" title={t("itemNotes.open")} onClick={() => dispatch({ type: "openNote", note: { project: note.project, label: note.label } })}>
              {note.project === item.project ? note.label : `${note.project} · ${note.label}`}
            </button>
            <span className="note-link-title">{note.summary}</span>
            <span className={`badge note-${note.status}`}>{t(`note.status.${note.status}` as MessageKey)}</span>
            <span className="hint">{t(`note.link.role.${note.role}` as MessageKey)}</span>
          </li>
        ))}
      </ul>
      {open.map((notice) => {
        const text = describeNotice(notice);
        return (
          <div key={notice.id} className="warn-box item-notice">
            <div>{t(text.key, text.params)}</div>
            <button className="btn small" disabled={acknowledge.isPending} onClick={() => acknowledge.mutate({ id: notice.id })}>
              {t("itemNotes.acknowledge")}
            </button>
          </div>
        );
      })}
      {acknowledge.error && (
        <div className="field-error" role="alert">
          {describeError(i18n, acknowledge.error)}
        </div>
      )}
    </section>
  );
}
