import { useState } from "react";
import type { MessageKey } from "../i18n/messages";
import { noteStatusColor } from "../domain/colors";
import { formatDate, type IndexNote, type IndexTopic, type NoteTreeProject, type NoteTreeTopic } from "../domain/notes";
import { useI18n } from "../i18n/i18n";
import type { NoteRef } from "../state/uiState";
import { useUiState } from "../state/useUiStateStore";
import { IconButton } from "./IconButton";
import { TopicDeleteDialog, TopicDialog, type TopicDialogMode } from "./TopicDialogs";

interface NoteTreeProps {
  tree: readonly NoteTreeProject[];
  /** All topics, for the choice of a parent in the dialogs. */
  allTopics: readonly IndexTopic[];
  projects: readonly string[];
  selected: NoteRef | null;
  /** While searching every node is open, whatever was collapsed. */
  searching: boolean;
  onSelect: (note: NoteRef) => void;
  onCreateNote: (project: string, topic: string | null) => void;
}

const REASONS = ["trigger", "notice", "topic_due", "review_expired"];

/** Notes as a tree like the backlog: project → topic → sub-topic → note. The actions of a topic sit in its row. */
export function NoteTree({ tree, allTopics, projects, selected, searching, onSelect, onCreateNote }: NoteTreeProps) {
  const { t, lang } = useI18n();
  const { state, dispatch } = useUiState();
  const [dialog, setDialog] = useState<TopicDialogMode | null>(null);
  const [deleting, setDeleting] = useState<IndexTopic | null>(null);
  const isOpen = (key: string) => searching || !state.collapsed.has(key);

  const caret = (key: string, hasChildren: boolean) => {
    const open = isOpen(key);
    return (
      <button
        className="caret"
        disabled={!hasChildren || searching}
        aria-label={hasChildren ? (open ? t("topic.collapse") : t("topic.expand")) : undefined}
        aria-expanded={hasChildren ? open : undefined}
        title={hasChildren ? (open ? t("topic.collapse") : t("topic.expand")) : undefined}
        onClick={() => dispatch({ type: "toggleCollapsed", uid: key })}
      >
        {hasChildren ? (open ? "▼" : "▶") : ""}
      </button>
    );
  };

  const noteRow = (note: IndexNote) => {
    const isSelected = selected?.project === note.project && selected.label === note.label;
    const reason = note.reason && REASONS.includes(note.reason) ? t(`note.reason.${note.reason}` as MessageKey) : null;
    return (
      <li key={`${note.project}/${note.label}`} className="nt-node">
        <div className="nt-line">
          <span className="caret" />
          <button className={`nt-note${isSelected ? " selected" : ""}`} aria-pressed={isSelected} onClick={() => onSelect({ project: note.project, label: note.label })}>
            <span className="nt-summary-line">
              <span className="dot" style={{ background: noteStatusColor(note.status) }} />
              <span className="nt-summary">{note.summary}</span>
            </span>
            <span className="note-meta">
              <span className={`badge note-${note.status}`}>{t(`note.status.${note.status}` as MessageKey)}</span>
              {reason && <span className="note-reason">{reason}</span>}
              {note.review_at && <span className="note-review">{t("notes.review", { d: formatDate(note.review_at, lang) })}</span>}
              <span className="note-label">{note.label}</span>
            </span>
          </button>
        </div>
      </li>
    );
  };

  const topicRow = (node: NoteTreeTopic) => {
    const { topic } = node;
    const hasChildren = node.children.length > 0 || node.notes.length > 0;
    return (
      <li key={node.key} className="nt-node">
        <div className="nt-line nt-topic">
          {caret(node.key, hasChildren)}
          <span className="nt-name">{topic.name}</span>
          {topic.due && <span className="badge due" title={t("notes.due")}>!</span>}
          <span className="topic-count" title={t("notes.countHint", { n: node.count })}>{node.count}</span>
          <span className="nt-actions">
            <IconButton icon="plus" label={t("notes.newNoteIn", { t: topic.name })} onClick={() => onCreateNote(topic.project, topic.label)} />
            <IconButton icon="subfolderPlus" label={t("topic.newChild")} onClick={() => setDialog({ kind: "create", project: topic.project, parent: topic })} />
            <IconButton icon="rename" label={t("topic.rename")} onClick={() => setDialog({ kind: "rename", topic })} />
            <IconButton icon="calendar" label={t("topic.due")} onClick={() => setDialog({ kind: "due", topic })} />
            <IconButton icon="move" label={t("topic.move")} onClick={() => setDialog({ kind: "move", topic })} />
            <IconButton icon="trash" label={t("topic.delete")} variant="danger" onClick={() => setDeleting(topic)} />
          </span>
        </div>
        {hasChildren && isOpen(node.key) && (
          <ul className="nt-list nt-children">
            {node.children.map(topicRow)}
            {node.notes.map(noteRow)}
          </ul>
        )}
      </li>
    );
  };

  return (
    <div className="note-tree">
      {tree.map((p) => {
        const hasChildren = p.topics.length > 0 || p.withoutTopic.length > 0;
        return (
          <section key={p.key} className="nt-project" aria-label={p.project}>
            <div className="nt-line nt-project-line">
              {caret(p.key, hasChildren)}
              <span className="nt-name project-title">{`${p.project} (${p.count})`}</span>
              <span className="nt-actions">
                <IconButton icon="plus" label={t("notes.newNoteNoTopic")} onClick={() => onCreateNote(p.project, null)} />
                <IconButton icon="folderPlus" label={t("notes.newTopicIn", { p: p.project })} onClick={() => setDialog({ kind: "create", project: p.project, parent: null })} />
              </span>
            </div>
            {hasChildren && isOpen(p.key) && (
              <ul className="nt-list nt-children">
                {p.topics.map(topicRow)}
                {p.withoutTopic.length > 0 && (
                  <li className="nt-node">
                    <div className="nt-line nt-topic">
                      {caret(p.withoutTopicKey, true)}
                      <span className="nt-name nt-none">{t("notes.noTopic")}</span>
                      <span className="topic-count">{p.withoutTopic.length}</span>
                    </div>
                    {isOpen(p.withoutTopicKey) && <ul className="nt-list nt-children">{p.withoutTopic.map(noteRow)}</ul>}
                  </li>
                )}
              </ul>
            )}
          </section>
        );
      })}
      {dialog && <TopicDialog mode={dialog} topics={allTopics} projects={projects} onClose={() => setDialog(null)} />}
      {deleting && <TopicDeleteDialog topic={deleting} onClose={() => setDeleting(null)} onDeleted={() => setDeleting(null)} />}
    </div>
  );
}
