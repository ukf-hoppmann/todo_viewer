import { useEffect, useRef, useState } from "react";
import { useDecideNotice, useDueList, useDueNoteAction, useNote, useNoteNotices } from "../api/queries";
import { describeNotice, type DueNote, groupDueByReason, nextAfterAction, type Notice, type RowAction, rowActions, rowKey } from "../domain/due";
import type { Item } from "../domain/model";
import { describeTrigger } from "../domain/notes";
import { describeError, useI18n } from "../i18n/i18n";
import type { MessageKey } from "../i18n/messages";
import { useUiState } from "../state/useUiStateStore";
import { Modal } from "./Modal";
import { PromoteNoteDialog } from "./PromoteNoteDialog";
import { SnoozeDialog } from "./SnoozeDialog";

interface DueModalProps {
  items: readonly Item[];
  projects: readonly string[];
  onClose: () => void;
}

type Dialog = { kind: "snooze" | "promote"; note: DueNote; notice?: Notice };

const LABELS: Record<RowAction, MessageKey> = {
  snooze: "snooze.button",
  done: "note.action.done",
  dropped: "note.action.dropped",
  promote: "promote.button",
  keep: "note.action.keep",
  detach: "due.action.detach",
  drop: "due.action.drop",
  open: "due.action.open",
};

/**
 * Everything that needs attention, grouped by reason, with the actions for each note. A row stays until its action
 * has worked on the server; a failed action leaves it with the error. The list closes when nothing is left.
 */
export function DueModal({ items, projects, onClose }: DueModalProps) {
  const i18n = useI18n();
  const { t, lang } = i18n;
  const { dispatch } = useUiState();
  const list = useDueList(true);
  const quick = useDueNoteAction();
  const decide = useDecideNotice();
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const [focusKey, setFocusKey] = useState<string | null>(null);
  const hadRows = useRef(false);

  const notes = list.data ?? [];
  const groups = groupDueByReason(notes);
  const keys = groups.flatMap((g) => g.notes.map(rowKey));
  const keyList = keys.join("\n");

  useEffect(() => {
    if (notes.length > 0) hadRows.current = true;
    else if (list.isSuccess && hadRows.current) onClose();
  }, [notes.length, list.isSuccess, onClose]);

  useEffect(() => {
    if (focusKey === null) return;
    const row = [...document.querySelectorAll<HTMLElement>("[data-row]")].find((el) => el.dataset.row === focusKey);
    row?.querySelector<HTMLElement>("button")?.focus();
  }, [focusKey, keyList]);

  /** Runs an action for a row: on success the list is read again and the next row gets the focus; on failure the row
   *  stays and shows what went wrong. */
  const run = async (note: DueNote, action: () => Promise<unknown>) => {
    const key = rowKey(note);
    setErrors((e) => ({ ...e, [key]: "" }));
    try {
      await action();
      setFocusKey(nextAfterAction(keys, key));
    } catch (error) {
      setErrors((e) => ({ ...e, [key]: t("due.actionFailed", { e: describeError(i18n, error) }) }));
    }
  };

  const perform = (note: DueNote, action: RowAction, notice?: Notice) => {
    if (action === "open") {
      dispatch({ type: "openNote", note: { project: note.project, label: note.label } });
      onClose();
    } else if (action === "snooze" || action === "promote") {
      setDialog({ kind: action, note, notice });
    } else if (notice) {
      void run(note, () => decide.mutateAsync({ id: notice.id, decision: action as "keep" | "detach" | "drop" }));
    } else if (action === "done" || action === "dropped" || action === "keep") {
      void run(note, () => quick.mutateAsync({ project: note.project, label: note.label, action }));
    }
  };

  return (
    <Modal labelledBy="due-title" onDismiss={onClose} className="due-modal">
      <div className="doc-head">
        <h3 id="due-title">{t("due.title")}</h3>
        <button className="btn small" onClick={onClose}>
          {t("close")}
        </button>
      </div>
      {list.isLoading && <div className="hint">{t("due.loading")}</div>}
      {list.error && <div className="field-error" role="alert">{t("err.load", { e: describeError(i18n, list.error) })}</div>}
      {list.isSuccess && notes.length === 0 && <div className="hint">{t("due.empty")}</div>}
      <div className="due-list">
        {groups.map((group) => (
          <section key={group.reason} className="due-group">
            <h4>{t("due.group", { reason: t(`note.reason.${group.reason}` as MessageKey), n: group.notes.length })}</h4>
            {group.notes.map((note) => {
              const key = rowKey(note);
              const fired = note.triggers.map((trigger) => describeTrigger(trigger, lang)).filter((x) => x.fired);
              return (
                <div key={key} className="due-row" data-row={key}>
                  <div className="due-row-head">
                    <span className="note-summary">{note.summary}</span>
                    <span className="note-label">{`${note.project} · ${note.label}`}</span>
                  </div>
                  {note.topic_path.length > 0 && <div className="hint">{note.topic_path.join(" › ")}</div>}
                  {note.reason === "trigger" &&
                    fired.map((text, n) => (
                      <div key={n} className="hint">
                        {t("due.fired", { text: t(text.key, text.params) })}
                      </div>
                    ))}
                  {note.reason === "notice" ? (
                    <NoticeLines note={note} onAct={(action, notice) => perform(note, action, notice)} />
                  ) : (
                    <RowButtons actions={rowActions(note)} onAct={(action) => perform(note, action)} />
                  )}
                  {errors[key] && (
                    <div className="field-error" role="alert">
                      {errors[key]}
                    </div>
                  )}
                </div>
              );
            })}
          </section>
        ))}
      </div>
      {dialog?.kind === "snooze" && (
        <SnoozeFromDue
          note={dialog.note}
          projects={projects}
          items={items}
          onClose={() => setDialog(null)}
          onDone={() => setFocusKey(nextAfterAction(keys, rowKey(dialog.note)))}
        />
      )}
      {dialog?.kind === "promote" && (
        <PromoteFromDue note={dialog.note} notice={dialog.notice} items={items} onClose={() => setDialog(null)} />
      )}
    </Modal>
  );
}

function RowButtons({ actions, onAct }: { actions: readonly RowAction[]; onAct: (action: RowAction) => void }) {
  const { t } = useI18n();
  return (
    <div className="due-actions">
      {actions.map((action) => (
        <button key={action} className="btn small" onClick={() => onAct(action)}>
          {t(LABELS[action])}
        </button>
      ))}
    </div>
  );
}

/** A note that is due because of change notices: each open notice says what happened and is decided on its own. */
function NoticeLines({ note, onAct }: { note: DueNote; onAct: (action: RowAction, notice?: Notice) => void }) {
  const { t } = useI18n();
  const notices = useNoteNotices(note.project, note.label);
  const actions = rowActions(note);
  return (
    <>
      {(notices.data ?? []).map((notice) => {
        const text = describeNotice(notice);
        return (
          <div key={notice.id} className="due-notice">
            <div>{t(text.key, text.params)}</div>
            <RowButtons actions={actions.filter((a) => a !== "open")} onAct={(action) => onAct(action, notice)} />
          </div>
        );
      })}
      <RowButtons actions={["open"]} onAct={(action) => onAct(action)} />
    </>
  );
}

/** The snooze dialog needs the note's current version; it is read when the dialog opens. */
function SnoozeFromDue({ note, projects, items, onClose, onDone }: { note: DueNote; projects: readonly string[]; items: readonly Item[]; onClose: () => void; onDone: () => void }) {
  const current = useNote(note.project, note.label);
  if (!current.data) return null;
  return <SnoozeDialog project={note.project} label={note.label} version={current.data.version} projects={projects} items={items} onClose={onClose} onDone={onDone} />;
}

/** The promote dialog needs the note's text and version; they are read when the dialog opens. */
function PromoteFromDue({ note, notice, items, onClose }: { note: DueNote; notice?: Notice; items: readonly Item[]; onClose: () => void }) {
  const current = useNote(note.project, note.label);
  if (!current.data) return null;
  return <PromoteNoteDialog note={current.data} items={items} notice={notice ? { id: notice.id } : undefined} onClose={onClose} />;
}
