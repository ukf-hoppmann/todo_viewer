import { useState } from "react";
import { ApiError } from "../api/client";
import { useDeleteNote, useFinishNote, useKeepNote, useNote, useUpdateNote } from "../api/queries";
import type { Item } from "../domain/model";
import { formatDate, type IndexNote, type IndexTopic } from "../domain/notes";
import { describeError, useI18n } from "../i18n/i18n";
import type { MessageKey } from "../i18n/messages";
import type { NoteRef } from "../state/uiState";
import { Markdown } from "./DocumentDialog";
import { Modal } from "./Modal";
import { NoteDocuments } from "./NoteDocuments";
import { NoteLinks } from "./NoteLinks";
import { NoteOrigin } from "./OriginLink";
import { PromoteNoteDialog } from "./PromoteNoteDialog";
import { SnoozeDialog } from "./SnoozeDialog";
import { TriggerEditor } from "./TriggerEditor";

interface NoteDetailProps {
  note: NoteRef;
  projects: readonly string[];
  topics: readonly IndexTopic[];
  notes: readonly IndexNote[];
  items: readonly Item[];
  onClose: () => void;
  onOpenNote: (note: NoteRef) => void;
}

/** One note: summary, long text, state, the actions that need no trigger, its links and its documents. */
export function NoteDetail({ note: ref, projects, topics, notes, items, onClose, onOpenNote }: NoteDetailProps) {
  const i18n = useI18n();
  const { t, lang } = i18n;
  const query = useNote(ref.project, ref.label);
  const update = useUpdateNote();
  const finish = useFinishNote();
  const keep = useKeepNote();
  const [draft, setDraft] = useState<{ summary: string; body: string; topic: string; version: string } | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [snoozing, setSnoozing] = useState(false);
  const [promoting, setPromoting] = useState(false);
  const data = query.data;

  if (query.error && !data) {
    return (
      <aside className="note-detail">
        <div className="load-error">{t("err.load", { e: describeError(i18n, query.error) })}</div>
      </aside>
    );
  }
  if (!data) return <aside className="note-detail hint">{t("note.detail.loading")}</aside>;

  const readOnly = data.archived || data.deleted !== null;
  const conflict = update.error instanceof ApiError && update.error.code === "version_conflict";
  const topicsOfProject = topics.filter((x) => x.project === data.project);
  const topicName = topicsOfProject.find((x) => x.label === data.topic)?.path.join(" › ");
  const actionError = finish.error ?? keep.error;

  const startEdit = () => setDraft({ summary: data.summary, body: data.body ?? "", topic: data.topic ?? "", version: data.version });
  const save = () => {
    if (!draft) return;
    update.mutate(
      {
        project: data.project,
        label: data.label,
        version: draft.version,
        summary: draft.summary.trim(),
        body: draft.body.trim() === "" ? null : draft.body,
        topic: draft.topic === "" ? null : draft.topic,
      },
      { onSuccess: () => setDraft(null) },
    );
  };
  const reload = async () => {
    update.reset();
    const fresh = (await query.refetch()).data;
    if (fresh) setDraft({ summary: fresh.summary, body: fresh.body ?? "", topic: fresh.topic ?? "", version: fresh.version });
  };

  return (
    <aside className="note-detail">
      <div className="note-detail-head">
        <span className="note-label">{`${data.project} · ${data.label}`}</span>
        <button className="btn small" onClick={onClose}>
          {t("close")}
        </button>
      </div>

      {draft ? (
        <form
          className="edit-form"
          aria-label={t("note.detail.edit")}
          onSubmit={(e) => {
            e.preventDefault();
            save();
          }}
        >
          <label className="field">
            {t("note.detail.summary")}
            <input autoFocus value={draft.summary} onChange={(e) => setDraft({ ...draft, summary: e.target.value })} />
          </label>
          <label className="field">
            {t("note.detail.body")}
            <textarea value={draft.body} onChange={(e) => setDraft({ ...draft, body: e.target.value })} />
          </label>
          <label className="field">
            {t("note.detail.topic")}
            <select value={draft.topic} onChange={(e) => setDraft({ ...draft, topic: e.target.value })}>
              <option value="">{t("note.detail.noTopic")}</option>
              {topicsOfProject.map((x) => (
                <option key={x.label} value={x.label}>
                  {x.path.join(" › ")}
                </option>
              ))}
            </select>
          </label>
          {update.error && (
            <div className="field-error" role="alert">
              {conflict ? t("note.detail.conflict") : t("err.save", { e: describeError(i18n, update.error) })}
              {conflict && (
                <button type="button" className="btn small" onClick={reload}>
                  {t("note.detail.reload")}
                </button>
              )}
            </div>
          )}
          <div className="modal-actions">
            <button
              type="button"
              className="btn"
              onClick={() => {
                update.reset();
                setDraft(null);
              }}
            >
              {t("cancel")}
            </button>
            <button type="submit" className="btn primary" disabled={update.isPending || draft.summary.trim() === ""}>
              {update.isPending ? t("saving") : t("save")}
            </button>
          </div>
        </form>
      ) : (
        <>
          <h2 className="note-title">{data.summary}</h2>
          <div className="note-facts">
            <span className={`badge note-${data.status}`}>{t(`note.status.${data.status}` as MessageKey)}</span>
            {data.reason && <span className="note-reason">{t(`note.reason.${data.reason}` as MessageKey)}</span>}
            {topicName && <span className="hint">{topicName}</span>}
            {data.review_at && (
              <span className="hint">
                {t("note.detail.reviewAt")}: {formatDate(data.review_at, lang)}
              </span>
            )}
          </div>
          <NoteOrigin project={data.project} label={data.label} promoted={data.status === "promoted"} />
          {data.body ? <Markdown text={data.body} /> : <div className="hint">{t("note.detail.noBody")}</div>}
          {readOnly ? (
            <div className="hint warn-box">{t("note.detail.closedHint")}</div>
          ) : (
            <div className="detail-actions note-actions">
              <button className="btn small" onClick={startEdit}>
                {t("note.detail.edit")}
              </button>
              <button className="btn small" onClick={() => setPromoting(true)}>
                {t("promote.button")}
              </button>
              <button className="btn small" disabled={finish.isPending} onClick={() => finish.mutate({ project: data.project, label: data.label, version: data.version, status: "done" })}>
                {t("note.action.done")}
              </button>
              <button className="btn small" disabled={finish.isPending} onClick={() => finish.mutate({ project: data.project, label: data.label, version: data.version, status: "dropped" })}>
                {t("note.action.dropped")}
              </button>
              <button className="btn small" onClick={() => setSnoozing(true)}>
                {t("snooze.button")}
              </button>
              <button className="btn small" disabled={keep.isPending} onClick={() => keep.mutate({ project: data.project, label: data.label, version: data.version })}>
                {t("note.action.keep")}
              </button>
              <button className="btn small danger" onClick={() => setDeleting(true)}>
                {t("note.action.delete")}
              </button>
            </div>
          )}
          {actionError && (
            <div className="field-error" role="alert">
              {t("err.save", { e: describeError(i18n, actionError) })}
            </div>
          )}
        </>
      )}

      <TriggerEditor
        project={data.project}
        label={data.label}
        triggers={data.triggers}
        topic={topicsOfProject.find((x) => x.label === data.topic)}
        projects={projects}
        items={items}
        readOnly={readOnly}
      />
      <NoteLinks
        project={data.project}
        label={data.label}
        readOnly={readOnly}
        projects={projects}
        topics={topics}
        notes={notes}
        items={items}
        onOpenNote={onOpenNote}
      />
      <NoteDocuments project={data.project} label={data.label} summary={data.summary} readOnly={readOnly} />

      {promoting && <PromoteNoteDialog note={data} items={items} onClose={() => setPromoting(false)} />}
      {snoozing && (
        <SnoozeDialog
          project={data.project}
          label={data.label}
          version={data.version}
          projects={projects}
          items={items}
          onClose={() => setSnoozing(false)}
        />
      )}
      {deleting && <NoteDeleteDialog project={data.project} label={data.label} onClose={() => setDeleting(false)} onDeleted={onClose} />}
    </aside>
  );
}

function NoteDeleteDialog({ project, label, onClose, onDeleted }: { project: string; label: string; onClose: () => void; onDeleted: () => void }) {
  const i18n = useI18n();
  const { t } = i18n;
  const remove = useDeleteNote();
  return (
    <Modal labelledBy="note-delete-title" onDismiss={onClose}>
      <h3 id="note-delete-title">{t("note.delete.title", { label })}</h3>
      <p>{t("note.delete.text")}</p>
      {remove.error && (
        <div className="field-error" role="alert">
          {describeError(i18n, remove.error)}
        </div>
      )}
      <div className="modal-actions">
        <button className="btn" onClick={onClose}>
          {t("cancel")}
        </button>
        <button className="btn danger" disabled={remove.isPending} onClick={() => remove.mutate({ project, label }, { onSuccess: onDeleted })}>
          {t("note.delete.confirm")}
        </button>
      </div>
    </Modal>
  );
}
