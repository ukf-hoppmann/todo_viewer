import {
  Background,
  Controls,
  type Edge,
  Handle,
  MarkerType,
  type Node,
  type NodeProps,
  Position,
  ReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { type MouseEvent, memo, useCallback, useEffect, useMemo, useState } from "react";
import { priorityColor, statusColor } from "../domain/colors";
import { ProgressPie } from "../components/ProgressPie";
import { dependencyGraph, itemProgress, type Item, type Progress, type Uid } from "../domain/model";
import { useI18n } from "../i18n/i18n";
import { useUiState } from "../state/useUiStateStore";
import { focusNeighborhood, layoutGraph } from "./graphLayout";

type ItemNode = Node<{ item: Item; progress: Progress | null; selected: boolean; dimmed: boolean }, "item">;
type Positions = Map<Uid, { x: number; y: number }>;

const TITLE_LIMIT = 28;

const ItemNodeView = memo(function ItemNodeView({ data }: NodeProps<ItemNode>) {
  const { item, progress, selected, dimmed } = data;
  const { vocab } = useI18n();
  const title = item.title.length > TITLE_LIMIT ? `${item.title.slice(0, TITLE_LIMIT)}…` : item.title;
  return (
    <div className={`graph-node${selected ? " selected" : ""}${dimmed ? " dimmed" : ""}`} style={{ borderColor: statusColor(item.status) }} title={item.title}>
      <Handle type="target" position={Position.Left} />
      <div className="g-id">
        <span
          className="dot"
          title={item.priority ? `${vocab("field", "Priority")}: ${vocab("priority", item.priority)}` : ""}
          style={{ background: priorityColor(item.priority) }}
        />
        {item.ref.id}
        {progress && <ProgressPie progress={progress} />}
      </div>
      <div>{title}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
});

const NODE_TYPES = { item: ItemNodeView };

interface GraphViewProps {
  visible: Item[];
  /** All items, unfiltered; progress is computed over these. */
  items: Item[];
  onSelect: (uid: Uid | null) => void;
}

const NO_UIDS: ReadonlySet<Uid> = new Set();

/**
 * Items with dependencies; isolated items are hidden. Zoom and pan survive data updates.
 * The selected node, nodes marked with a modifier click, and the hovered node are highlighted
 * together with their edges and direct neighbors.
 */
export function GraphView({ visible, items, onSelect }: GraphViewProps) {
  const { t } = useI18n();
  const { state } = useUiState();
  const graph = useMemo(() => dependencyGraph(visible), [visible]);
  const progress = useMemo(() => itemProgress(items), [items]);
  const [layout, setLayout] = useState<{ graph: typeof graph; positions: Positions } | null>(null);
  const [hoveredId, setHoveredId] = useState<Uid | null>(null);
  const [marked, setMarked] = useState<ReadonlySet<Uid>>(NO_UIDS);

  // ELK lays out asynchronously; render the last finished layout so nodes and positions always match.
  useEffect(() => {
    let cancelled = false;
    void layoutGraph(graph).then((positions) => {
      if (!cancelled) setLayout({ graph, positions });
    });
    return () => {
      cancelled = true;
    };
  }, [graph]);

  const shown = layout?.graph;
  const focus = useMemo(() => {
    const set = new Set(marked);
    if (state.selectedId && shown?.nodes.some((n) => n.uid === state.selectedId)) set.add(state.selectedId);
    if (hoveredId) set.add(hoveredId);
    return set;
  }, [marked, state.selectedId, hoveredId, shown]);
  const neighborhood = useMemo(() => (shown ? focusNeighborhood(shown, focus) : new Set<Uid>()), [shown, focus]);

  const reset = useCallback(() => {
    setMarked(NO_UIDS);
    onSelect(null);
  }, [onSelect]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") reset();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [reset]);

  // Plain click selects, or deselects the selected node. A modifier click toggles an extra highlight.
  const onNodeClick = (event: MouseEvent, uid: Uid) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey) {
      if (uid === state.selectedId) onSelect(null);
      else setMarked((prev) => toggled(prev, uid));
      return;
    }
    setMarked(NO_UIDS);
    onSelect(uid === state.selectedId ? null : uid);
  };

  const nodes: ItemNode[] = useMemo(
    () =>
      (layout?.graph.nodes ?? []).map((item) => ({
        id: item.uid,
        type: "item",
        position: layout?.positions.get(item.uid) ?? { x: 0, y: 0 },
        data: {
          item,
          progress: progress.get(item.uid) ?? null,
          selected: item.uid === state.selectedId || marked.has(item.uid),
          dimmed: neighborhood.size > 0 && !neighborhood.has(item.uid),
        },
        draggable: false,
        connectable: false,
      })),
    [layout, progress, state.selectedId, marked, neighborhood],
  );
  const edges: Edge[] = useMemo(
    () =>
      (layout?.graph.edges ?? []).map((e) => {
        const active = focus.has(e.from) || focus.has(e.to);
        const opacity = focus.size === 0 ? 0.6 : active ? 1 : 0.12;
        return {
          id: `${e.from}->${e.to}`,
          source: e.from,
          target: e.to,
          zIndex: active ? 1 : 0,
          markerEnd: { type: MarkerType.ArrowClosed, color: "var(--accent)" },
          style: { stroke: "var(--accent)", strokeOpacity: opacity, strokeWidth: active ? 2 : 1 },
        };
      }),
    [layout, focus],
  );

  return (
    <div className="view graph-view">
      <div className="graph-info">
        <span>{t("graph.info", { n: graph.nodes.length, total: visible.length })}</span>
        <span>{t("graph.hint")}</span>
      </div>
      <div className="graph-canvas">
        {layout && (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={NODE_TYPES}
            colorMode="dark"
            fitView
            minZoom={0.1}
            nodesConnectable={false}
            onNodeClick={(event, node) => onNodeClick(event, node.id)}
            onPaneClick={reset}
            onNodeMouseEnter={(_, node) => setHoveredId(node.id)}
            onNodeMouseLeave={() => setHoveredId(null)}
          >
            <Background />
            <Controls showInteractive={false} />
          </ReactFlow>
        )}
      </div>
    </div>
  );
}

function toggled(set: ReadonlySet<Uid>, uid: Uid): ReadonlySet<Uid> {
  const next = new Set(set);
  if (!next.delete(uid)) next.add(uid);
  return next;
}
