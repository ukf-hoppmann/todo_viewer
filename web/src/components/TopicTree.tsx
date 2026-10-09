import { useMemo, useState } from "react";
import { buildTopicTree, type IndexTopic, type TopicNode } from "../domain/notes";
import { useI18n } from "../i18n/i18n";
import type { NoteRef } from "../state/uiState";
import { IconButton } from "./IconButton";
import { TopicDeleteDialog, TopicDialog, type TopicDialogMode } from "./TopicDialogs";

interface TopicTreeProps {
  /** The topics to show (already limited to the chosen project, if any). */
  topics: readonly IndexTopic[];
  /** All topics, for the choice of a parent. */
  allTopics: readonly IndexTopic[];
  projects: readonly string[];
  /** The project a new topic starts in. */
  defaultProject: string;
  selected: NoteRef | null;
  onSelect: (topic: NoteRef | null) => void;
}

const sameTopic = (a: NoteRef | null, b: IndexTopic) => a !== null && a.project === b.project && a.label === b.label;

/** The topic tree with the actions on the chosen topic: new sub-topic, rename, move, delete. */
export function TopicTree({ topics, allTopics, projects, defaultProject, selected, onSelect }: TopicTreeProps) {
  const { t } = useI18n();
  const tree = useMemo(() => buildTopicTree(topics), [topics]);
  const [dialog, setDialog] = useState<TopicDialogMode | null>(null);
  const [deleting, setDeleting] = useState<IndexTopic | null>(null);
  const chosen = topics.find((x) => sameTopic(selected, x)) ?? null;
  const showProjects = new Set(topics.map((x) => x.project)).size > 1;

  const [collapsed, setCollapsed] = useState<ReadonlySet<string>>(new Set());
  const toggle = (key: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (!next.delete(key)) next.add(key);
      return next;
    });

  const render = (node: TopicNode) => {
    const key = `${node.topic.project}/${node.topic.label}`;
    const hasChildren = node.children.length > 0;
    const isCollapsed = collapsed.has(key);
    return (
      <li key={key} className="topic-node">
        <div className="topic-line">
          <button
            className="caret"
            disabled={!hasChildren}
            aria-label={isCollapsed ? t("topic.expand") : t("topic.collapse")}
            aria-expanded={hasChildren ? !isCollapsed : undefined}
            title={hasChildren ? (isCollapsed ? t("topic.expand") : t("topic.collapse")) : undefined}
            onClick={() => toggle(key)}
          >
            {hasChildren ? (isCollapsed ? "▶" : "▼") : ""}
          </button>
          <button
            className={`topic-row${sameTopic(selected, node.topic) ? " selected" : ""}`}
            aria-pressed={sameTopic(selected, node.topic)}
            onClick={() => onSelect({ project: node.topic.project, label: node.topic.label })}
          >
            <span className="topic-name">{node.topic.name}</span>
            {node.topic.due && <span className="badge due" title={t("notes.due")}>!</span>}
            <span
              className="topic-count"
              title={hasChildren ? t("notes.totalHint", { total: node.total, direct: node.topic.note_count }) : undefined}
            >
              {node.total}
            </span>
          </button>
        </div>
        {hasChildren && !isCollapsed && <ul className="topic-list topic-children">{node.children.map(render)}</ul>}
      </li>
    );
  };

  const groups = tree.reduce<{ project: string; roots: TopicNode[] }[]>((acc, root) => {
    const last = acc[acc.length - 1];
    if (last?.project === root.topic.project) last.roots.push(root);
    else acc.push({ project: root.topic.project, roots: [root] });
    return acc;
  }, []);

  return (
    <div className="topic-tree">
      <div className="topic-tools">
        <IconButton icon="folderPlus" label={t("notes.newTopic")} onClick={() => setDialog({ kind: "create", project: chosen?.project ?? defaultProject, parent: null })} />
        {chosen && (
          <>
            <IconButton icon="subfolderPlus" label={t("topic.newChild")} onClick={() => setDialog({ kind: "create", project: chosen.project, parent: chosen })} />
            <IconButton icon="rename" label={t("topic.rename")} onClick={() => setDialog({ kind: "rename", topic: chosen })} />
            <IconButton icon="calendar" label={t("topic.due")} onClick={() => setDialog({ kind: "due", topic: chosen })} />
            <IconButton icon="move" label={t("topic.move")} onClick={() => setDialog({ kind: "move", topic: chosen })} />
            <IconButton icon="trash" label={t("topic.delete")} variant="danger" onClick={() => setDeleting(chosen)} />
          </>
        )}
      </div>
      <button className={`topic-row all${selected === null ? " selected" : ""}`} aria-pressed={selected === null} onClick={() => onSelect(null)}>
        <span className="topic-name">{t("notes.allNotes")}</span>
      </button>
      {groups.map((group) => (
        <div key={group.project}>
          {showProjects && <h4 className="topic-project">{group.project}</h4>}
          <ul className="topic-list">{group.roots.map(render)}</ul>
        </div>
      ))}
      {dialog && <TopicDialog mode={dialog} topics={allTopics} projects={projects} onClose={() => setDialog(null)} />}
      {deleting && (
        <TopicDeleteDialog
          topic={deleting}
          onClose={() => setDeleting(null)}
          onDeleted={() => {
            if (sameTopic(selected, deleting)) onSelect(null);
            setDeleting(null);
          }}
        />
      )}
    </div>
  );
}
