import { Box, Typography } from "@mui/material";
import { Background, Controls, MarkerType, ReactFlow, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useMemo, useState, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import { useProjectSelection, useSearchText } from "../../workspace";
import { useListItemsQuery } from "../api";
import { GraphNode, type ItemNode } from "../GraphNode";
import { layoutGraph } from "../graphLayout";
import { dependencyGraph, highlight, toggled, type DependencyGraph } from "../graphModel";
import { ItemDetail } from "../ItemDetail";
import { filterItems } from "../model";
import { useBacklogState } from "../state";
import { backlogTestIds } from "../testIds";

const NODE_TYPES = { item: GraphNode };
const NO_UIDS: ReadonlySet<string> = new Set();
const EDGE_COLOR = "#5b8cff";

/**
 * The dependencies between the items as a directed graph, dependencies at the left. Only items that take part in
 * a dependency are shown, filtered like the tree. Selecting, hovering and a click with ⌘/Ctrl/⇧ highlight the node,
 * its edges and its direct neighbors; Esc, a click on the background or on the selected node clears the highlight.
 */
export default function GraphPage() {
	const { t } = useTranslation("backlog");
	const { visible } = useProjectSelection();
	const [search] = useSearchText();
	const state = useBacklogState();
	const projectUids = useMemo(() => visible.map((project) => project.uid), [visible]);
	const { data: items = [] } = useListItemsQuery(projectUids, { skip: projectUids.length === 0 });
	const shown = useMemo(
		() => filterItems(items, { hiddenStatuses: new Set(state.hiddenStatuses), hiddenPriorities: new Set(state.hiddenPriorities), search }),
		[items, state.hiddenStatuses, state.hiddenPriorities, search],
	);
	const graph = useMemo(() => dependencyGraph(shown), [shown]);
	const [layout, setLayout] = useState<{ graph: DependencyGraph; positions: Map<string, { x: number; y: number }> }>();
	const [hovered, setHovered] = useState<string | null>(null);
	const [marked, setMarked] = useState<ReadonlySet<string>>(NO_UIDS);
	const { selected, setSelected } = state;

	// ELK lays out asynchronously: the last finished layout is drawn, so nodes and positions always match.
	useEffect(() => {
		let cancelled = false;
		void layoutGraph(graph).then((positions) => {
			if (!cancelled) setLayout({ graph, positions });
		});
		return () => {
			cancelled = true;
		};
	}, [graph]);

	const drawn = layout?.graph;
	const emphasis = useMemo(() => highlight(drawn ?? { nodes: [], edges: [] }, selected, marked, hovered), [drawn, selected, marked, hovered]);

	const reset = useCallback(() => {
		setMarked(NO_UIDS);
		setSelected(null);
	}, [setSelected]);

	useEffect(() => {
		const onKey = (event: KeyboardEvent) => {
			if (event.key === "Escape") reset();
		};
		window.addEventListener("keydown", onKey);
		return () => window.removeEventListener("keydown", onKey);
	}, [reset]);

	// A plain click selects (or deselects the selected node); a click with a modifier marks an extra node.
	const onNodeClick = (event: MouseEvent, uid: string) => {
		if (event.metaKey || event.ctrlKey || event.shiftKey) {
			if (uid === selected) setSelected(null);
			else setMarked((current) => toggled(current, uid));
			return;
		}
		setMarked(NO_UIDS);
		setSelected(uid === selected ? null : uid);
	};

	const nodes: ItemNode[] = useMemo(
		() =>
			(drawn?.nodes ?? []).map((item) => ({
				id: item.uid,
				type: "item" as const,
				position: layout?.positions.get(item.uid) ?? { x: 0, y: 0 },
				data: { item, selected: item.uid === selected || marked.has(item.uid), dimmed: emphasis.dimmed(item.uid) },
				draggable: false,
				connectable: false,
			})),
		[drawn, layout, selected, marked, emphasis],
	);
	const edges: Edge[] = useMemo(
		() =>
			(drawn?.edges ?? []).map((edge) => {
				const active = emphasis.active(edge);
				const opacity = emphasis.focus.size === 0 ? 0.6 : active ? 1 : 0.12;
				return {
					id: `${edge.from}->${edge.to}`,
					source: edge.from,
					target: edge.to,
					zIndex: active ? 1 : 0,
					data: { active },
					markerEnd: { type: MarkerType.ArrowClosed, color: EDGE_COLOR },
					style: { stroke: EDGE_COLOR, strokeOpacity: opacity, strokeWidth: active ? 2 : 1 },
				};
			}),
		[drawn, emphasis],
	);

	return (
		<Box sx={{ display: "flex", gap: 2, p: 2, alignItems: "stretch", flex: 1, minHeight: 0 }} data-testid={backlogTestIds.graph}>
			<Box sx={{ flex: "1 1 60%", minWidth: 0, display: "flex", flexDirection: "column" }}>
				<Box sx={{ display: "flex", justifyContent: "space-between", gap: 2, mb: 1 }}>
					<Typography variant="caption" color="text.secondary" data-testid={backlogTestIds.graphInfo}>
						{t("graph.info", { n: graph.nodes.length, total: shown.length })}
					</Typography>
					<Typography variant="caption" color="text.secondary">
						{t("graph.hint")}
					</Typography>
				</Box>
				{graph.nodes.length === 0 ? (
					<Typography color="text.secondary" data-testid={backlogTestIds.graphEmpty}>
						{t("graph.empty")}
					</Typography>
				) : (
					<Box sx={{ flexGrow: 1, minHeight: 300, border: 1, borderColor: "divider" }}>
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
								onNodeMouseEnter={(_, node) => setHovered(node.id)}
								onNodeMouseLeave={() => setHovered(null)}
							>
								<Background />
								<Controls showInteractive={false} />
							</ReactFlow>
						)}
					</Box>
				)}
			</Box>
			{selected && (
				<Box sx={{ flex: "1 1 40%", minWidth: 0, overflowY: "auto" }}>
					<ItemDetail uid={selected} onSelect={setSelected} onClose={() => setSelected(null)} />
				</Box>
			)}
		</Box>
	);
}
