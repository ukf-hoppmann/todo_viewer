import { useState } from "react";
import { useCreateNote } from "../api/queries";
import type { IndexTopic } from "../domain/notes";
import { describeError, useI18n } from "../i18n/i18n";
import type { NoteRef } from "../state/uiState";
import { Modal } from "./Modal";

interface NoteCreateDialogProps {
  projects: readonly string[];
  topics: readonly IndexTopic[];
  /** Project and topic the dialog starts with. */
  project: string;
  topic: string | null;
  onClose: () => void;
  onCreated: (note: NoteRef) => void;
}

/** Creates a note: a one-line summary, an optional long text, and a topic of the same project. */
export function NoteCreateDialog({ projects, topics, project: initialProject, topic: initialTopic, onClose, onCreated }: NoteCreateDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const create = useCreateNote();
  const [project, setProject] = useState(initialProject);
  const [summary, setSummary] = useState("");
  const [body, setBody] = useState("");
  const [topic, setTopic] = useState(initialTopic ?? "");

  const submit = () =>
    create.mutate(
      { project, summary: summary.trim(), body: body.trim() === "" ? null : body, topic: topic || null, trigger_mode: "any" },
      { onSuccess: (note) => onCreated({ project: note.project, label: note.label }) },
    );

  return (
    <Modal labelledBy="note-create-title" onDismiss={onClose}>
      <form
        className="edit-form"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <h3 id="note-create-title">{t("note.create.title")}</h3>
        {projects.length > 1 && (
          <label className="field">
            {t("note.create.project")}
            <select
              value={project}
              onChange={(e) => {
                setProject(e.target.value);
                setTopic("");
              }}
            >
              {projects.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="field">
          {t("note.create.summary")}
          <input autoFocus value={summary} onChange={(e) => setSummary(e.target.value)} />
        </label>
        <label className="field">
          {t("note.create.body")}
          <textarea value={body} onChange={(e) => setBody(e.target.value)} />
        </label>
        <label className="field">
          {t("note.create.topic")}
          <select value={topic} onChange={(e) => setTopic(e.target.value)}>
            <option value="">{t("note.create.noTopic")}</option>
            {topics
              .filter((x) => x.project === project)
              .map((x) => (
                <option key={x.label} value={x.label}>
                  {x.path.join(" › ")}
                </option>
              ))}
          </select>
        </label>
        {create.error && (
          <div className="field-error" role="alert">
            {t("err.save", { e: describeError(i18n, create.error) })}
          </div>
        )}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            {t("cancel")}
          </button>
          <button type="submit" className="btn primary" disabled={create.isPending || summary.trim() === "" || project === ""}>
            {create.isPending ? t("saving") : t("note.create.submit")}
          </button>
        </div>
      </form>
    </Modal>
  );
}
