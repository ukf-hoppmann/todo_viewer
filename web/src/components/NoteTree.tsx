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

/** The keys of every topic node (and „Ohne Topic“) in the tree, for collapsing or expanding all at once. */
function topicKeys(tree: readonly NoteTreeProject[]): string[] {
  const walk = (nodes: readonly NoteTreeTopic[]): string[] => nodes.flatMap((n) => [n.key, ...walk(n.children)]);
  return tree.flatMap((p) => [...walk(p.topics), ...(p.withoutTopic.length > 0 ? [p.withoutTopicKey] : [])]);
}

/** Notes laid out like the backlog tree: per project the topics, sub-topics and notes, one line each. The actions of a
 *  topic sit in its line. */
export function NoteTree({ tree, allTopics, projects, selected, searching, onSelect, onCreateNote }: NoteTreeProps) {
  const { t, lang } = useI18n();
  const { state, dispatch } = useUiState();
  const [dialog, setDialog] = useState<TopicDialogMode | null>(null);
  const [deleting, setDeleting] = useState<IndexTopic | null>(null);
  const isOpen = (key: string) => searching || !state.collapsed.has(key);
  const keys = topicKeys(tree);
  // Extended marking: the whole area of a topic on level 1 and 2 gets its own background.
  const level = (depth: number) => (state.notesHighlight && depth <= 2 ? ` nt-level-${depth}` : "");
  const allCollapsed = keys.length > 0 && keys.every((k) => state.collapsed.has(k));

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
        {hasChildren ? (open ? "▾" : "▸") : ""}
      </button>
    );
  };

  const noteNode = (note: IndexNote) => {
    const isSelected = selected?.project === note.project && selected.label === note.label;
    const reason = note.reason && REASONS.includes(note.reason) ? t(`note.reason.${note.reason}` as MessageKey) : null;
    const color = noteStatusColor(note.status);
    const status = t(`note.status.${note.status}` as MessageKey);
    return (
      <div key={`${note.project}/${note.label}`} className="tree-node">
        <div className="node-line">
          <span className="caret" />
          <button
            className={`node-row nt-note${isSelected ? " selected" : ""}`}
            aria-pressed={isSelected}
            title={note.summary}
            onClick={() => onSelect({ project: note.project, label: note.label })}
          >
            <span className="dot" title={status} style={{ background: color }} />
            <span className="node-type" title={status} style={{ background: color, color: "var(--on-color)" }}>
              {t("notes.typeNote")}
            </span>
            <span className="node-title">
              {`${note.label} — `}
              <span className="nt-summary">{note.summary}</span>
            </span>
            {reason && <span className="node-progress">{reason}</span>}
            {note.review_at && <span className="node-progress">{t("notes.review", { d: formatDate(note.review_at, lang) })}</span>}
          </button>
        </div>
      </div>
    );
  };

  const topicNode = (node: NoteTreeTopic, depth: number) => {
    const { topic } = node;
    const hasChildren = node.children.length > 0 || node.notes.length > 0;
    return (
      <div key={node.key} className={`tree-node${level(depth)}`}>
        <div className="node-line">
          {caret(node.key, hasChildren)}
          <div className="node-row nt-topic">
            <span className="dot" style={{ background: topic.due ? "var(--status-rejected)" : "var(--prio-none)" }} />
            <span className="node-type">{t("notes.typeTopic")}</span>
            <span className="node-title">{topic.name}</span>
            {topic.due && <span className="badge due" title={t("notes.due")}>!</span>}
            <span className="node-progress" title={t("notes.countHint", { n: node.count })}>{node.count}</span>
            <span className="nt-actions">
              <IconButton icon="plus" label={t("notes.newNoteIn", { t: topic.name })} onClick={() => onCreateNote(topic.project, topic.label)} />
              <IconButton icon="subfolderPlus" label={t("topic.newChild")} onClick={() => setDialog({ kind: "create", project: topic.project, parent: topic })} />
              <IconButton icon="rename" label={t("topic.rename")} onClick={() => setDialog({ kind: "rename", topic })} />
              <IconButton icon="calendar" label={t("topic.due")} onClick={() => setDialog({ kind: "due", topic })} />
              <IconButton icon="move" label={t("topic.move")} onClick={() => setDialog({ kind: "move", topic })} />
              <IconButton icon="trash" label={t("topic.delete")} variant="danger" onClick={() => setDeleting(topic)} />
            </span>
          </div>
        </div>
        {hasChildren && isOpen(node.key) && (
          <div className="node-children">
            {node.children.map((child) => topicNode(child, depth + 1))}
            {node.notes.map(noteNode)}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="note-tree">
      <div className="collapse-bar">
        <button
          className="btn small"
          disabled={keys.length === 0 || searching}
          onClick={() => dispatch({ type: "setCollapsed", uids: keys, collapsed: !allCollapsed })}
        >
          {t(allCollapsed ? "notes.expandTopics" : "notes.collapseTopics")}
        </button>
      </div>
      {tree.map((p) => (
        <section key={p.key} className="project-group" aria-label={p.project}>
          <div className="project-title nt-project">
            <span>{`${p.project} (${p.count})`}</span>
            <span className="nt-actions">
              <IconButton icon="plus" label={t("notes.newNoteNoTopic")} onClick={() => onCreateNote(p.project, null)} />
              <IconButton icon="folderPlus" label={t("notes.newTopicIn", { p: p.project })} onClick={() => setDialog({ kind: "create", project: p.project, parent: null })} />
            </span>
          </div>
          <div className="nt-project-bar" />
          {p.topics.map((node) => topicNode(node, 1))}
          {p.withoutTopic.length > 0 && (
            <div className={`tree-node${level(1)}`}>
              <div className="node-line">
                {caret(p.withoutTopicKey, true)}
                <div className="node-row nt-topic">
                  <span className="dot" style={{ background: "var(--prio-none)" }} />
                  <span className="node-type">{t("notes.typeTopic")}</span>
                  <span className="node-title nt-none">{t("notes.noTopic")}</span>
                  <span className="node-progress">{p.withoutTopic.length}</span>
                </div>
              </div>
              {isOpen(p.withoutTopicKey) && <div className="node-children">{p.withoutTopic.map(noteNode)}</div>}
            </div>
          )}
        </section>
      ))}
      {dialog && <TopicDialog mode={dialog} topics={allTopics} projects={projects} onClose={() => setDialog(null)} />}
      {deleting && <TopicDeleteDialog topic={deleting} onClose={() => setDeleting(null)} onDeleted={() => setDeleting(null)} />}
    </div>
  );
}
