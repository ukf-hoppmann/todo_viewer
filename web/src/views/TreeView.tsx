import { useMemo } from "react";
import { priorityColor, statusColor } from "../domain/colors";
import { ProgressPie } from "../components/ProgressPie";
import { buildTrees, collapsibleUids, type Item, type TreeNode, type Uid } from "../domain/model";
import { useI18n } from "../i18n/i18n";
import type { MessageKey } from "../i18n/messages";
import { useUiState } from "../state/useUiStateStore";

interface TreeViewProps {
  visible: Item[];
  items: Item[];
  onSelect: (uid: Uid) => void;
}

/** Epic → Story → Task per project, with progress over all items of the project. */
export function TreeView({ visible, items, onSelect }: TreeViewProps) {
  const { t } = useI18n();
  const trees = useMemo(() => buildTrees(visible, items), [visible, items]);

  if (trees.length === 0) return <div className="view"><p className="empty-hint">{t("empty")}</p></div>;

  return (
    <div className="view tree-view">
      <CollapseBar items={items} />
      {trees.map(({ project, progress, roots }) => (
        <section key={project} className="project-group">
          <div className="project-title">{`${project} (${progress.done}/${progress.total})`}</div>
          <div className="progress-bar" role="progressbar" aria-valuenow={progress.done} aria-valuemax={progress.total}>
            <div className="progress-bar-fill" style={{ width: progress.total ? `${(progress.done / progress.total) * 100}%` : "0%" }} />
          </div>
          {roots.map((node) => (
            <TreeNodeRow key={node.item.key} node={node} onSelect={onSelect} />
          ))}
        </section>
      ))}
    </div>
  );
}

function TreeNodeRow({ node, onSelect }: { node: TreeNode; onSelect: (uid: Uid) => void }) {
  const { vocab } = useI18n();
  const { state, dispatch } = useUiState();
  const { item, optional, progress, children } = node;
  const hasChildren = children.length > 0;
  const collapsed = hasChildren && state.collapsed.has(item.uid);
  const color = priorityColor(item.priority);

  return (
    <div className={`tree-node${optional ? " optional" : ""}`}>
      <div className="node-line">
        <button
          className="caret"
          disabled={!hasChildren}
          aria-label={hasChildren ? (collapsed ? "expand" : "collapse") : undefined}
          aria-expanded={hasChildren ? !collapsed : undefined}
          onClick={() => dispatch({ type: "toggleCollapsed", uid: item.uid })}
        >
          {hasChildren ? (collapsed ? "▸" : "▾") : ""}
        </button>
        <button className={`node-row${item.uid === state.selectedId ? " selected" : ""}`} onClick={() => onSelect(item.uid)}>
          <span
            className="dot"
            title={item.priority ? `${vocab("field", "Priority")}: ${vocab("priority", item.priority)}` : ""}
            style={{ background: color, ["--dot-color" as string]: color }}
          />
          <span
            className="node-type"
            title={vocab("status", item.status)}
            style={{ background: statusColor(item.status), color: "var(--on-color)" }}
          >
            {vocab("type", item.type)}
          </span>
          <span className="node-title">{`${item.id} — ${item.title}`}</span>
          {progress && <ProgressPie progress={progress} />}
        </button>
      </div>
      {hasChildren && !collapsed && (
        <div className="node-children">
          {children.map((child) => (
            <TreeNodeRow key={child.item.key} node={child} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  );
}

const COLLAPSE_LABELS: Record<"Epic" | "Story", [MessageKey, MessageKey]> = {
  Epic: ["tree.collapseEpic", "tree.expandEpic"],
  Story: ["tree.collapseStory", "tree.expandStory"],
};

/** Collapses or expands all epics or stories of the marked projects (all projects when none is marked). */
function CollapseBar({ items }: { items: Item[] }) {
  const { t } = useI18n();
  const { state, dispatch } = useUiState();
  const scope = [...state.markedProjects].sort().join(", ") || t("tree.scopeAll");

  return (
    <div className="collapse-bar">
      {(["Epic", "Story"] as const).map((type) => {
        const uids = collapsibleUids(items, type, state.markedProjects);
        const allCollapsed = uids.length > 0 && uids.every((uid) => state.collapsed.has(uid));
        return (
          <button
            key={type}
            className="btn small"
            disabled={uids.length === 0}
            title={t("tree.scope", { p: scope })}
            onClick={() => dispatch({ type: "setCollapsed", uids, collapsed: !allCollapsed })}
          >
            {t(COLLAPSE_LABELS[type][allCollapsed ? 1 : 0])}
          </button>
        );
      })}
    </div>
  );
}
