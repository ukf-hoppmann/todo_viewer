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
import { memo, useMemo } from "react";
import { priorityColor, statusColor } from "../domain/colors";
import { dependencyGraph, type Item, type Uid } from "../domain/model";
import { useI18n } from "../i18n/i18n";
import { useUiState } from "../state/useUiStateStore";
import { layoutGraph } from "./graphLayout";

type ItemNode = Node<{ item: Item; selected: boolean }, "item">;

const TITLE_LIMIT = 28;

const ItemNodeView = memo(function ItemNodeView({ data }: NodeProps<ItemNode>) {
  const { item, selected } = data;
  const { vocab } = useI18n();
  const title = item.title.length > TITLE_LIMIT ? `${item.title.slice(0, TITLE_LIMIT)}…` : item.title;
  return (
    <div className={`graph-node${selected ? " selected" : ""}`} style={{ borderColor: statusColor(item.status) }} title={item.title}>
      <Handle type="target" position={Position.Left} />
      <div className="g-id">
        <span
          className="dot"
          title={item.priority ? `${vocab("field", "Priority")}: ${vocab("priority", item.priority)}` : ""}
          style={{ background: priorityColor(item.priority) }}
        />
        {item.ref.id}
      </div>
      <div>{title}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
});

const NODE_TYPES = { item: ItemNodeView };

interface GraphViewProps {
  visible: Item[];
  onSelect: (uid: Uid) => void;
}

/** Items with dependencies; isolated items are hidden. Zoom and pan survive data updates. */
export function GraphView({ visible, onSelect }: GraphViewProps) {
  const { t } = useI18n();
  const { state } = useUiState();
  const graph = useMemo(() => dependencyGraph(visible), [visible]);
  const positions = useMemo(() => layoutGraph(graph), [graph]);

  const nodes: ItemNode[] = useMemo(
    () =>
      graph.nodes.map((item) => ({
        id: item.uid,
        type: "item",
        position: positions.get(item.uid) ?? { x: 0, y: 0 },
        data: { item, selected: item.uid === state.selectedId },
        draggable: false,
        connectable: false,
      })),
    [graph, positions, state.selectedId],
  );
  const edges: Edge[] = useMemo(
    () =>
      graph.edges.map((e) => ({
        id: `${e.from}->${e.to}`,
        source: e.from,
        target: e.to,
        markerEnd: { type: MarkerType.ArrowClosed, color: "var(--accent)" },
        style: { stroke: "var(--accent)", strokeOpacity: 0.6 },
      })),
    [graph],
  );

  return (
    <div className="view graph-view">
      <div className="graph-info">{t("graph.info", { n: graph.nodes.length, total: visible.length })}</div>
      <div className="graph-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={NODE_TYPES}
          colorMode="dark"
          fitView
          minZoom={0.1}
          nodesConnectable={false}
          onNodeClick={(_, node) => onSelect(node.id)}
        >
          <Background />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </div>
  );
}
