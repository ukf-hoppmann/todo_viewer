import { useState } from "react";
import { ApiError } from "../api/client";
import { useCreateTopic, useDeleteTopic, useMoveTopic, useUpdateTopic } from "../api/queries";
import { type IndexTopic, topicSubtree } from "../domain/notes";
import { describeError, useI18n } from "../i18n/i18n";
import { Modal } from "./Modal";

export type TopicDialogMode =
  | { kind: "create"; project: string; parent: IndexTopic | null }
  | { kind: "rename"; topic: IndexTopic }
  | { kind: "move"; topic: IndexTopic };

interface TopicDialogProps {
  mode: TopicDialogMode;
  /** All topics of all projects, for the choice of a parent. */
  topics: readonly IndexTopic[];
  /** The projects a topic can be created in. */
  projects: readonly string[];
  onClose: () => void;
}

/** Creates, renames or moves a topic; the server checks the depth and loops and its error is shown as text. */
export function TopicDialog({ mode, topics, projects, onClose }: TopicDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const create = useCreateTopic();
  const update = useUpdateTopic();
  const move = useMoveTopic();
  const [project, setProject] = useState(mode.kind === "create" ? mode.project : mode.topic.project);
  const [name, setName] = useState(mode.kind === "rename" ? mode.topic.name : "");
  const [parent, setParent] = useState<string>(
    mode.kind === "create" ? (mode.parent?.label ?? "") : mode.kind === "move" ? (mode.topic.parent ?? "") : "",
  );

  const excluded = mode.kind === "move" ? topicSubtree(topics, project, mode.topic.label) : new Set<string>();
  const candidates = topics.filter((x) => x.project === project && !excluded.has(x.label));
  const mutation = mode.kind === "create" ? create : mode.kind === "rename" ? update : move;

  const submit = () => {
    const done = { onSuccess: onClose };
    if (mode.kind === "create") create.mutate({ project, name: name.trim(), parent: parent || null }, done);
    else if (mode.kind === "rename") update.mutate({ project, label: mode.topic.label, name: name.trim() }, done);
    else move.mutate({ project, label: mode.topic.label, parent: parent || null }, done);
  };

  const title =
    mode.kind === "create"
      ? mode.parent
        ? t("topic.dialog.childTitle", { name: mode.parent.name })
        : t("topic.dialog.createTitle")
      : mode.kind === "rename"
        ? t("topic.dialog.renameTitle")
        : t("topic.dialog.moveTitle", { name: mode.topic.name });
  const needsName = mode.kind !== "move";
  const needsParent = mode.kind !== "rename";

  return (
    <Modal labelledBy="topic-title" onDismiss={onClose}>
      <form
        className="edit-form"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <h3 id="topic-title">{title}</h3>
        {mode.kind === "create" && projects.length > 1 && !mode.parent && (
          <label className="field">
            {t("topic.dialog.project")}
            <select
              value={project}
              onChange={(e) => {
                setProject(e.target.value);
                setParent("");
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
        {needsName && (
          <label className="field">
            {t("topic.dialog.name")}
            <input autoFocus value={name} onChange={(e) => setName(e.target.value)} />
          </label>
        )}
        {needsParent && (
          <label className="field">
            {t("topic.dialog.parent")}
            <select value={parent} onChange={(e) => setParent(e.target.value)}>
              <option value="">{t("topic.dialog.root")}</option>
              {candidates.map((x) => (
                <option key={x.label} value={x.label}>
                  {[...x.path].join(" › ")}
                </option>
              ))}
            </select>
          </label>
        )}
        {mutation.error && (
          <div className="field-error" role="alert">
            {t("err.save", { e: describeError(i18n, mutation.error) })}
          </div>
        )}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            {t("cancel")}
          </button>
          <button type="submit" className="btn primary" disabled={mutation.isPending || (needsName && name.trim() === "")}>
            {mutation.isPending ? t("saving") : t("topic.dialog.save")}
          </button>
        </div>
      </form>
    </Modal>
  );
}

interface TopicDeleteDialogProps {
  topic: IndexTopic;
  onClose: () => void;
  onDeleted: () => void;
}

/** Moves a topic to the trash; one with content asks again before taking the content along. */
export function TopicDeleteDialog({ topic, onClose, onDeleted }: TopicDeleteDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const remove = useDeleteTopic();
  const [content, setContent] = useState<string | null>(null);

  const submit = (cascade: boolean) =>
    remove.mutate(
      { project: topic.project, label: topic.label, cascade },
      {
        onSuccess: onDeleted,
        onError: (e) => {
          if (e instanceof ApiError && e.code === "topic_has_content") setContent(e.details.items ?? "");
        },
      },
    );
  const otherError = remove.error && !(remove.error instanceof ApiError && remove.error.code === "topic_has_content");

  return (
    <Modal labelledBy="topic-delete-title" onDismiss={onClose}>
      <h3 id="topic-delete-title">{t("topic.delete.title", { name: topic.name })}</h3>
      <p>{t("topic.delete.text")}</p>
      {content !== null && (
        <div className="hint warn-box" role="alert">
          {t("topic.delete.content", { items: content })}
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
        <button className="btn danger" disabled={remove.isPending} onClick={() => submit(content !== null)}>
          {content === null ? t("topic.delete.confirm") : t("topic.delete.cascade")}
        </button>
      </div>
    </Modal>
  );
}
