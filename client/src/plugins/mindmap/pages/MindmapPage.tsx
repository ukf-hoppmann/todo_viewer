import { Alert, Box, Breadcrumbs, Link, Typography } from "@mui/material";
import { Background, Controls, ReactFlow, type Edge, type ReactFlowInstance } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { usePageDetail } from "../../../core";
import { useShownStatuses } from "../../backlog";
import { useDeleteElement, useProjectSelection } from "../../workspace";
import { errorMessage, useAssignItemMutation, useCreateNodeMutation, useGetTreeQuery, useMoveNodeMutation, useUpdateNodeMutation, type ItemRefOut, type TreeNodeOut } from "../api";
import { canDropItem, dropPlacement, filterByMark, filterByState, focusPath, isOpen, shownProject, toggledFold, visibleNodes, type DropZone } from "../domain/tree";
import { MapActionsContext, type MapActions } from "../mapActions";
import { layoutTree } from "../mindmapLayout";
import { MindmapNode, type TopicNode } from "../MindmapNode";
import { useMapNavigation } from "../navigation";
import { NodeDetail } from "../NodeDetail";
import { UnassignedPanel } from "../UnassignedPanel";
import { useMindmapState } from "../state";
import { mindmapTestIds } from "../testIds";

const NODE_TYPES = { topic: MindmapNode };
const NO_NODES: readonly TreeNodeOut[] = [];
const NO_ITEMS: readonly ItemRefOut[] = [];
const DOUBLE_CLICK_MS = 250;
const FIT = { maxZoom: 1, padding: 0.15 };
const EDGE_STYLE = { stroke: "#5b8cff", strokeOpacity: 0.7 };

type Structure = Array<{ id: string; parentId: string | null }>;

/**
 * The topic tree of one project as a mind map to the side: the project is the root, every node hangs right of its
 * parent. Which project: the marked one, else the only visible one. Nodes are added, renamed and moved to the trash
 * in the map; a click opens title and text in the detail column. Dragging a node onto another one moves it with its
 * branch (below the target or next to it); only places `dropPlacement` allows are offered. What is folded is kept in the UI state of the
 * server; before the first choice two levels are open.
 */
export default function MindmapPage() {
	const { t } = useTranslation("mindmap");
	const { visible, marked } = useProjectSelection();
	const project = shownProject(visible, marked);
	const statuses = useShownStatuses();
	const { currentData: tree } = useGetTreeQuery({ project: project?.uid ?? "", statuses }, { skip: !project });
	const nodes = tree?.nodes ?? NO_NODES;
	const unassigned = tree?.unassigned ?? NO_ITEMS;
	const { fold, setFold, selected, setSelected, hiddenStates, hiddenMarks, showUnassigned } = useMindmapState();
	const [createNode] = useCreateNodeMutation();
	const [updateNode] = useUpdateNodeMutation();
	const [moveNode] = useMoveNodeMutation();
	const [assignItem] = useAssignItemMutation();
	// The drag in progress: the dragged node (or an item of the side view) and the place it is over, if that place is offered.
	const [drag, setDrag] = useState<{ source: string; over?: { id: string; zone: DropZone } }>();
	const dragSource = useRef<string | undefined>(undefined);
	const dragsItem = useRef(false);
	const { requestDelete, dialog: deleteDialog, failed: deleteFailed } = useDeleteElement();
	const [editing, setEditing] = useState<string | null>(null);
	const [error, setError] = useState<string>();
	const rootId = project?.uid;
	const { focus, openFocus } = useMapNavigation();

	// The focus from the address counts once the tree is loaded and only if it is a node of this tree; else the whole tree is shown.
	// `path` runs from the root to the focus (the root alone, and so no focus, for the root itself).
	const path = useMemo(() => (rootId && tree ? focusPath(rootId, nodes, focus) : null), [rootId, tree, nodes, focus]);
	const focusId = path && path.length > 1 ? path[path.length - 1] : undefined;
	const waitsForTree = Boolean(focus) && !tree;

	// The filters hide nodes by their state and mark; a hidden node takes its branch from the map. Moving still sees all nodes.
	const shown = useMemo(
		() => (rootId && !waitsForTree ? visibleNodes(rootId, filterByMark(filterByState(nodes, hiddenStates), hiddenMarks), fold, focusId) : []),
		[rootId, waitsForTree, nodes, fold, hiddenStates, hiddenMarks, focusId],
	);

	// The layout depends only on which nodes hang where, not on their titles: renaming keeps every node in place.
	const structureKey = JSON.stringify(shown.map(({ id, parentId }) => ({ id, parentId })));
	const [layout, setLayout] = useState<{ key: string; positions: Map<string, { x: number; y: number }> }>();
	useEffect(() => {
		let cancelled = false;
		void layoutTree(JSON.parse(structureKey) as Structure).then((positions) => {
			if (!cancelled) setLayout({ key: structureKey, positions });
		});
		return () => {
			cancelled = true;
		};
	}, [structureKey]);

	// When nodes appear or go (created, folded, deleted) or the detail column opens or closes (the map changes its
	// width), the map is fitted again, so no node is outside the view.
	const flow = useRef<ReactFlowInstance<TopicNode, Edge> | null>(null);
	const layoutKey = layout?.key;
	const detailOpen = Boolean(selected && nodes.some((node) => node.uid === selected));
	useEffect(() => {
		if (layoutKey === undefined) return;
		const timer = setTimeout(() => void flow.current?.fitView({ ...FIT, duration: 200 }), 50);
		return () => clearTimeout(timer);
	}, [layoutKey, detailOpen]);

	// The actions read the newest data through a ref, so the nodes of the map keep the same handlers.
	const latest = useRef({ shown, nodes, fold, rootId });
	useEffect(() => {
		latest.current = { shown, nodes, fold, rootId };
	});
	const actions: MapActions = useMemo(() => {
		const fail = (failure: unknown) => setError(errorMessage(failure, t("error.failed")));
		const depthOf = (id: string) => latest.current.shown.find((entry) => entry.id === id)?.depth ?? 0;
		const itemAllowed = (id: string) => {
			const { rootId: root, nodes: all } = latest.current;
			return Boolean(root) && canDropItem(root!, all, id);
		};
		const placementOf = (id: string, zone: DropZone) => {
			const { rootId: root, nodes: all } = latest.current;
			const source = dragSource.current;
			return root && source ? dropPlacement(root, all, source, id, zone) : null;
		};
		const endDrag = () => {
			dragSource.current = undefined;
			dragsItem.current = false;
			setDrag(undefined);
		};
		return {
			dragStart: (id) => {
				dragSource.current = id;
				setDrag({ source: id });
			},
			dragStartItem: (uid) => {
				dragSource.current = uid;
				dragsItem.current = true;
				setDrag({ source: uid });
			},
			dragEnd: endDrag,
			dragOver: (id, zone) => {
				const allowed = dragsItem.current ? itemAllowed(id) : placementOf(id, zone) !== null;
				const place = dragsItem.current ? "inside" : zone;
				// dragover fires continuously: the state object is kept while nothing changed, so nothing is drawn again.
				setDrag((current) => {
					if (!current) return current;
					if (!allowed) return current.over?.id === id ? { source: current.source } : current;
					return current.over?.id === id && current.over.zone === place ? current : { source: current.source, over: { id, zone: place } };
				});
				return allowed;
			},
			dragLeave: (id) => setDrag((current) => (current?.over?.id === id ? { source: current.source } : current)),
			drop: (id, zone) => {
				if (dragsItem.current) {
					const item = dragSource.current;
					const allowed = itemAllowed(id);
					endDrag();
					if (!item || !allowed) return;
					setError(undefined);
					assignItem({ node: id, item }).unwrap().catch(fail);
					return;
				}
				const placement = placementOf(id, zone);
				const node = latest.current.nodes.find((entry) => entry.uid === dragSource.current);
				endDrag();
				if (!placement || !node) return;
				setError(undefined);
				moveNode({ uid: node.uid, version: node.version, ...placement })
					.unwrap()
					.then(() => {
						// The moved branch must be visible: a closed target it was hung below is opened.
						if (zone === "inside") setFold((current) => (isOpen(current, id, depthOf(id)) ? current : toggledFold(current, id, depthOf(id))));
					})
					.catch(fail);
			},
			toggle: (id) => setFold((current) => toggledFold(current, id, depthOf(id))),
			add: (id) => {
				const { rootId: root } = latest.current;
				if (!root) return;
				setError(undefined);
				createNode({ project: root, title: t("node.new"), ...(id === root ? {} : { parent: id }) })
					.unwrap()
					.then((created) => {
						// The new child must be visible: a closed parent is opened.
						setFold((current) => (isOpen(current, id, depthOf(id)) ? current : toggledFold(current, id, depthOf(id))));
						setEditing(created.uid);
					})
					.catch(fail);
			},
			startRename: (id) => setEditing(id),
			cancelRename: () => setEditing(null),
			commitTitle: (id, title) => {
				setEditing(null);
				const node = latest.current.nodes.find((entry) => entry.uid === id);
				const wanted = title.trim();
				if (!node || wanted === "" || wanted === node.title) return;
				setError(undefined);
				updateNode({ uid: id, version: node.version, title: wanted }).unwrap().catch(fail);
			},
			remove: (id) => {
				const node = latest.current.nodes.find((entry) => entry.uid === id);
				if (!node) return;
				setError(undefined);
				void requestDelete(node.uid, node.version);
			},
			openAsRoot: (id) => openFocus(id),
		};
	}, [createNode, updateNode, moveNode, assignItem, requestDelete, setFold, openFocus, t]);

	// A double click renames and must not open the detail in between (the map would shift under the pointer): a click
	// selects only after the time a double click may take.
	const pendingClick = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
	useEffect(() => () => clearTimeout(pendingClick.current), []);
	const onNodeClick = (id: string) => {
		clearTimeout(pendingClick.current);
		if (id === rootId) return;
		pendingClick.current = setTimeout(() => setSelected((current) => (current === id ? null : id)), DOUBLE_CLICK_MS);
	};

	const open = selected ? nodes.find((node) => node.uid === selected) : undefined;
	const close = useCallback(() => setSelected(null), [setSelected]);
	usePageDetail(open && <NodeDetail key={open.uid} node={open} onClose={close} />);

	const flowNodes: TopicNode[] = useMemo(
		() =>
			shown.flatMap((entry) => {
				const position = layout?.positions.get(entry.id);
				if (!position) return [];
				return [
					{
						id: entry.id,
						type: "topic" as const,
						position,
						data: {
							id: entry.id,
							title: entry.node?.title ?? project?.name ?? "",
							isRoot: entry.node === undefined,
							hasChildren: entry.hasChildren,
							hasNotes: (entry.node?.documents.length ?? 0) > 0,
							state: entry.node?.state,
							mark: entry.node?.mark,
							total: entry.node?.total,
							done: entry.node?.done,
							open: entry.open,
							selected: entry.id === selected,
							editing: entry.id === editing,
							dragging: entry.id === drag?.source,
							drop: drag?.over?.id === entry.id ? drag.over.zone : undefined,
						},
						draggable: false,
						connectable: false,
					},
				];
			}),
		[shown, layout, project?.name, selected, editing, drag],
	);
	const edges: Edge[] = useMemo(
		() =>
			flowNodes.flatMap((node) => {
				const parentId = shown.find((entry) => entry.id === node.id)?.parentId;
				return parentId && layout?.positions.has(parentId) ? [{ id: `${parentId}->${node.id}`, source: parentId, target: node.id, style: EDGE_STYLE }] : [];
			}),
		[flowNodes, shown, layout],
	);

	if (!project) {
		return (
			<Box sx={{ p: 2 }} data-testid={mindmapTestIds.page}>
				<Typography color="text.secondary" data-testid={mindmapTestIds.chooseProject}>
					{t("page.chooseProject")}
				</Typography>
			</Box>
		);
	}
	const message = error ?? deleteFailed;
	return (
		<Box sx={{ p: 2, flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }} data-testid={mindmapTestIds.page}>
			{message && (
				<Alert severity="error" sx={{ mb: 1 }} onClose={error ? () => setError(undefined) : undefined} data-testid={mindmapTestIds.error}>
					{message}
				</Alert>
			)}
			{focusId && path && (
				<Breadcrumbs aria-label={t("page.path")} sx={{ mb: 1 }} data-testid={mindmapTestIds.path}>
					{path.map((id, index) => {
						const title = id === rootId ? project.name : (nodes.find((node) => node.uid === id)?.title ?? "");
						return index === path.length - 1 ? (
							<Typography key={id} color="text.primary" data-testid={mindmapTestIds.pathEntry(id)}>
								{title}
							</Typography>
						) : (
							<Link key={id} component="button" type="button" underline="hover" onClick={() => openFocus(id === rootId ? undefined : id)} data-testid={mindmapTestIds.pathEntry(id)}>
								{title}
							</Link>
						);
					})}
				</Breadcrumbs>
			)}
			<Typography variant="caption" color="text.secondary" sx={{ mb: 1 }}>
				{t("page.hint")}
			</Typography>
			<MapActionsContext.Provider value={actions}>
				<Box sx={{ flexGrow: 1, minHeight: 300, display: "flex" }}>
					<Box sx={{ flexGrow: 1, minWidth: 0, border: 1, borderColor: "divider" }} data-testid={mindmapTestIds.map}>
						{layout && (
							<ReactFlow
								key={project.uid}
								nodes={flowNodes}
								edges={edges}
								nodeTypes={NODE_TYPES}
								colorMode="dark"
								fitView
								fitViewOptions={FIT}
								onInit={(instance) => {
									flow.current = instance;
								}}
								minZoom={0.1}
								nodesConnectable={false}
								zoomOnDoubleClick={false}
								onNodeClick={(_, node) => onNodeClick(node.id)}
								onNodeDoubleClick={() => clearTimeout(pendingClick.current)}
							>
								<Background />
								<Controls showInteractive={false} />
							</ReactFlow>
						)}
					</Box>
					{showUnassigned && <UnassignedPanel items={unassigned} />}
				</Box>
			</MapActionsContext.Provider>
			{deleteDialog}
		</Box>
	);
}
