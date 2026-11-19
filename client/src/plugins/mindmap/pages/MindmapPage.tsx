import { Alert, Box, Breadcrumbs, Link, Typography } from "@mui/material";
import { Background, Controls, MarkerType, ReactFlow, type Edge, type ReactFlowInstance } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { usePageDetail } from "../../../core";
import { useShownStatuses } from "../../backlog";
import { useDeleteElement, useProjectSelection } from "../../workspace";
import { errorMessage, useAssignItemMutation, useCreateNodeMutation, useGetTreeQuery, useGetTreesQuery, useListMapsQuery, useMoveNodeMutation, useRemoveNodeFromMapMutation, useUpdateNodeMutation, type ItemRefOut, type NodeTreeOut, type TreeNodeOut } from "../api";
import { chooseMap } from "../domain/maps";
import { COMBINED_ROOT, canDropItem, combinedTree, dropPlacement, filterByMark, filterByState, focusPath, isOpen, liftLinks, shownProject, toggledFold, visibleNodes, type DropZone } from "../domain/tree";
import type { TreeOut } from "../api";
import { BranchDialog } from "../BranchDialog";
import type { BranchAction, BranchSource } from "../domain/branches";
import { MapActionsContext, type MapActions } from "../mapActions";
import { dropZonesOf, edgeSides, layoutTree } from "../mindmapLayout";
import { MindmapNode, type TopicNode } from "../MindmapNode";
import { useMapNavigation } from "../navigation";
import { NodeDetail } from "../NodeDetail";
import { DeleteSharedDialog, NodeMenu, TreeJumpMenu, type MenuAnchor } from "../NodeMenus";
import { UnassignedPanel } from "../UnassignedPanel";
import { useMindmapState } from "../state";
import { mindmapTestIds } from "../testIds";

const NODE_TYPES = { topic: MindmapNode };
const NO_NODES: readonly TreeNodeOut[] = [];
const NO_ITEMS: readonly ItemRefOut[] = [];
const DOUBLE_CLICK_MS = 250;
const FIT = { maxZoom: 1, padding: 0.15 };
const EDGE_STYLE = { stroke: "#5b8cff", strokeOpacity: 0.7 };
const LINK_COLOR = "#e0a83a";
const LINK_STYLE = { stroke: LINK_COLOR, strokeDasharray: "6 4", strokeWidth: 1.5 };

type Structure = Array<{ id: string; parentId: string | null }>;

/**
 * In the overall view (`view` "all") the root is common to all visible projects (it belongs to none and takes nothing), the projects are
 * its first nodes. The topic tree of one project as a mind map to the side: the project is the root, every node hangs right of its
 * parent. Which project: the marked one, else the only visible one. Nodes are added, renamed and moved to the trash
 * in the map; a click opens title and text in the detail column. Dragging a node onto another one moves it with its
 * branch (below the target or next to it), within its project; only places `dropPlacement` allows are offered. What is folded is kept in the UI state of the
 * server; before the first choice two levels are open.
 */
export default function MindmapPage() {
	const { t } = useTranslation("mindmap");
	const { visible, marked, mark } = useProjectSelection();
	const project = shownProject(visible, marked);
	const statuses = useShownStatuses();
	const { view, setView, chosenMaps, chooseMapOf, fold, setFold, selected, setSelected, hiddenStates, hiddenMarks, showUnassigned, showDependencies, highlightShared, layout: mode } = useMindmapState();
	const all = view === "all";
	// The single view loads the tree of one project, the overall view those of all visible projects.
	// The single view shows the map chosen in the sidebar list: the project tree, or a free map of the project (named by `tree`).
	const { currentData: maps } = useListMapsQuery(project?.uid ?? "", { skip: all || !project });
	const map = all ? undefined : chooseMap(maps, project ? chosenMaps[project.uid] : undefined);
	const freeTree = map?.kind === "free" ? (map.tree_uid ?? undefined) : undefined;
	const { currentData: single } = useGetTreeQuery({ project: project?.uid ?? "", statuses, ...(freeTree ? { tree: freeTree } : {}) }, { skip: all || !project || !map });
	const projectUids = useMemo(() => visible.map((entry) => entry.uid), [visible]);
	const { currentData: several } = useGetTreesQuery({ projects: projectUids, statuses }, { skip: !all || projectUids.length === 0 });
	// `byProject` holds the nodes of every project as the server gave them (top nodes without a parent); `nodes` is what the map draws from.
	const { nodes, byProject, tree, rootId, rootTitle, unassignedProject, unassigned } = useMemo(() => {
		if (!all) {
			const own = single?.nodes ?? NO_NODES;
			return { nodes: own, byProject: new Map([[project?.uid ?? "", own]]), tree: single, rootId: project?.uid, rootTitle: freeTree ? (map?.name ?? "") : (project?.name ?? ""), unassignedProject: freeTree ? undefined : project?.uid, unassigned: single?.unassigned ?? NO_ITEMS };
		}
		// A response that belongs to other projects (the selection just changed) is not used.
		const trees: readonly TreeOut[] | undefined = several && several.length === visible.length && several.every((entry, index) => entry.project_uid === visible[index]!.uid) ? several : undefined;
		const own = new Map(visible.map((entry, index) => [entry.uid, trees?.[index]?.nodes ?? NO_NODES]));
		const makeProject = (entry: (typeof visible)[number], sums: { position: number; total: number; done: number; state: string }): TreeNodeOut => ({
			uid: entry.uid, project_uid: entry.uid, label: "", title: entry.name, text: null, tree_uid: "", parent_uid: null, version: 0, documents: [], mark: null, tree_count: 1, ...sums,
		});
		const markedTree = marked ? trees?.[visible.findIndex((entry) => entry.uid === marked.uid)] : undefined;
		return {
			nodes: trees ? combinedTree(visible, trees.map((entry) => entry.nodes), makeProject) : NO_NODES,
			byProject: own,
			tree: trees,
			rootId: COMBINED_ROOT,
			rootTitle: t("page.allProjects"),
			unassignedProject: markedTree ? marked?.uid : undefined,
			unassigned: markedTree?.unassigned ?? NO_ITEMS,
		};
	}, [all, single, several, project, visible, marked, t, map, freeTree]);
	const [createNode] = useCreateNodeMutation();
	const [updateNode] = useUpdateNodeMutation();
	const [moveNode] = useMoveNodeMutation();
	const [removeFromMap] = useRemoveNodeFromMapMutation();
	const [assignItem] = useAssignItemMutation();
	// The drag in progress: the dragged node (or an item of the side view) and the place it is over, if that place is offered.
	const [drag, setDrag] = useState<{ source: string; over?: { id: string; zone: DropZone } }>();
	const dragSource = useRef<string | undefined>(undefined);
	const dragsItem = useRef(false);
	const { requestDelete, dialog: deleteDialog, failed: deleteFailed } = useDeleteElement();
	const [editing, setEditing] = useState<string | null>(null);
	// The menu of a node, the dialog that hangs over or transfers a branch, the list of trees to jump to, and the question before a shared node is deleted everywhere.
	const [menu, setMenu] = useState<{ id: string; anchor: MenuAnchor }>();
	const [branch, setBranch] = useState<{ source: BranchSource; action: BranchAction }>();
	const [trees, setTrees] = useState<{ id: string; anchor: MenuAnchor }>();
	const [sharedDelete, setSharedDelete] = useState<string>();
	const [error, setError] = useState<string>();
	const { focus, openFocus } = useMapNavigation();

	// The focus from the address counts once the tree is loaded and only if it is a node of this tree; else the whole tree is shown.
	// `path` runs from the root to the focus (the root alone, and so no focus, for the root itself).
	const path = useMemo(() => (rootId && tree ? focusPath(rootId, nodes, focus) : null), [rootId, tree, nodes, focus]);
	const focusId = path && path.length > 1 ? path[path.length - 1] : undefined;
	const waitsForTree = Boolean(focus) && !tree;
	// The root and, in the overall view, the project nodes are no records: they are neither opened in the detail nor renamed, moved or removed.
	const isFixed = (id: string) => id === rootId || (all && byProject.has(id));

	// The filters hide nodes by their state and mark; a hidden node takes its branch from the map. Moving still sees all nodes.
	const shown = useMemo(
		() => (rootId && !waitsForTree ? visibleNodes(rootId, filterByMark(filterByState(nodes, hiddenStates), hiddenMarks), fold, focusId) : []),
		[rootId, waitsForTree, nodes, fold, hiddenStates, hiddenMarks, focusId],
	);

	// The layout depends only on which nodes hang where and on the arrangement, not on their titles: renaming keeps every node in place.
	const structureKey = JSON.stringify(shown.map(({ id, parentId }) => ({ id, parentId })));
	const arrangementKey = `${mode}:${structureKey}`;
	const [layout, setLayout] = useState<{ key: string; positions: Map<string, { x: number; y: number }> }>();
	useEffect(() => {
		let cancelled = false;
		void layoutTree(JSON.parse(structureKey) as Structure, mode).then((positions) => {
			if (!cancelled) setLayout({ key: arrangementKey, positions });
		});
		return () => {
			cancelled = true;
		};
	}, [structureKey, mode, arrangementKey]);

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
	const latest = useRef({ shown, nodes, byProject, fold, unassignedProject, freeTree });
	useEffect(() => {
		latest.current = { shown, nodes, byProject, fold, unassignedProject, freeTree };
	});
	const actions: MapActions = useMemo(() => {
		const fail = (failure: unknown) => setError(errorMessage(failure, t("error.failed")));
		const depthOf = (id: string) => latest.current.shown.find((entry) => entry.id === id)?.depth ?? 0;
		// The project a node belongs to (a project node: itself) with its nodes as the server gave them; none for the common root.
		const scopeOf = (id: string) => {
			const { byProject: own, nodes: drawn } = latest.current;
			const projectUid = own.has(id) ? id : drawn.find((entry) => entry.uid === id)?.project_uid;
			const list = projectUid ? own.get(projectUid) : undefined;
			return projectUid && list ? { projectUid, list } : undefined;
		};
		const itemAllowed = (id: string) => {
			const scope = scopeOf(id);
			return Boolean(scope) && scope!.projectUid === latest.current.unassignedProject && canDropItem(scope!.projectUid, scope!.list, id);
		};
		// A node moves only within its project: the source must be a node of the target's project.
		const placementOf = (id: string, zone: DropZone) => {
			const scope = scopeOf(id);
			const source = dragSource.current;
			return scope && source ? dropPlacement(scope.projectUid, scope.list, source, id, zone) : null;
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
				const scope = scopeOf(id);
				if (!scope) return;
				setError(undefined);
				createNode({ project: scope.projectUid, title: t("node.new"), ...(id === scope.projectUid ? {} : { parent: id }), ...(latest.current.freeTree ? { tree: latest.current.freeTree } : {}) })
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
				// A node in several trees is deleted everywhere only after a question that names the trees.
				if (node.tree_count > 1) setSharedDelete(id);
				else void requestDelete(node.uid, node.version);
			},
			openMenu: (id, anchor) => setMenu({ id, anchor }),
			openTrees: (id, anchor) => setTrees({ id, anchor }),
			openAsRoot: (id) => openFocus(id),
		};
	}, [createNode, updateNode, moveNode, assignItem, requestDelete, setFold, openFocus, t]);

	// What the menu and the jump list do with a node of this page.
	const nodeOf = (id: string | undefined) => (id ? nodes.find((entry) => entry.uid === id) : undefined);
	const sourceOf = (node: TreeNodeOut): BranchSource => ({ uid: node.uid, version: node.version, title: node.title, project_uid: node.project_uid, tree_uid: node.tree_uid });
	const jump = (id: string, tree: NodeTreeOut) => {
		const node = nodeOf(id);
		setTrees(undefined);
		if (!node) return;
		if (all) {
			setView("single");
			mark(node.project_uid);
		}
		chooseMapOf(node.project_uid, tree.kind === "free" ? tree.tree_uid : null);
		setSelected(node.uid);
	};

	// A double click renames and must not open the detail in between (the map would shift under the pointer): a click
	// selects only after the time a double click may take.
	const pendingClick = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
	useEffect(() => () => clearTimeout(pendingClick.current), []);
	const onNodeClick = (id: string) => {
		clearTimeout(pendingClick.current);
		if (isFixed(id)) return;
		pendingClick.current = setTimeout(() => setSelected((current) => (current === id ? null : id)), DOUBLE_CLICK_MS);
	};

	const open = selected && !isFixed(selected) ? nodes.find((node) => node.uid === selected) : undefined;
	const close = useCallback(() => setSelected(null), [setSelected]);
	usePageDetail(open && <NodeDetail key={open.uid} node={open} onClose={close} />);

	const rootPosition = rootId ? layout?.positions.get(rootId) : undefined;
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
							title: entry.node?.title ?? rootTitle,
							isRoot: entry.node === undefined,
							isProject: all && byProject.has(entry.id),
							noAdd: all && entry.node === undefined,
							hasChildren: entry.hasChildren,
							hasNotes: (entry.node?.documents.length ?? 0) > 0,
							version: entry.node?.version,
							projectUid: entry.node?.project_uid,
							treeUid: entry.node?.tree_uid,
							treeCount: entry.node?.tree_count,
							frameShared: highlightShared,
							state: entry.node?.state,
							mark: entry.node?.mark,
							total: entry.node?.total,
							done: entry.node?.done,
							open: entry.open,
							selected: entry.id === selected,
							editing: entry.id === editing,
							dragging: entry.id === drag?.source,
							drop: drag?.over?.id === entry.id ? drag.over.zone : undefined,
							zones: entry.node && rootPosition ? dropZonesOf(mode, position, rootPosition) : "normal",
						},
						draggable: false,
						connectable: false,
					},
				];
			}),
		[shown, layout, rootPosition, mode, rootTitle, all, byProject, selected, editing, drag, highlightShared],
	);
	const treeEdges: Edge[] = useMemo(
		() =>
			flowNodes.flatMap((node) => {
				const parentId = shown.find((entry) => entry.id === node.id)?.parentId;
				const from = parentId ? layout?.positions.get(parentId) : undefined;
				if (!parentId || !from) return [];
				const { source, target } = edgeSides(mode, from, node.position);
				return [{ id: `${parentId}->${node.id}`, source: parentId, target: node.id, sourceHandle: source, targetHandle: target, style: EDGE_STYLE }];
			}),
		[flowNodes, shown, layout, mode],
	);
	// Dependencies between topics (switched on in the sidebar): the server sums them per pair of nodes, the map moves their ends to the
	// nearest shown node. They are drawn below the tree edges and cannot be clicked.
	const dependencyLinks = useMemo(() => {
		if (!showDependencies) return [];
		const lines = (all ? (tree as readonly TreeOut[] | undefined) : tree ? [tree as TreeOut] : undefined)?.flatMap((entry) => entry.links) ?? [];
		return liftLinks(lines, new Set(shown.map((entry) => entry.id)), new Map(nodes.map((node) => [node.uid, node.parent_uid])));
	}, [showDependencies, all, tree, shown, nodes]);
	const edges: Edge[] = useMemo(() => {
		const lines = dependencyLinks.flatMap((link) => {
			const from = layout?.positions.get(link.from_node);
			const to = layout?.positions.get(link.to_node);
			if (!from || !to) return [];
			const { source, target } = edgeSides(mode, from, to);
			return [
				{
					id: `dependency:${link.from_node}->${link.to_node}`,
					source: link.from_node,
					target: link.to_node,
					sourceHandle: source,
					targetHandle: target,
					style: LINK_STYLE,
					markerEnd: { type: MarkerType.ArrowClosed, color: LINK_COLOR },
					label: String(link.count),
					labelStyle: { fill: LINK_COLOR },
					selectable: false,
					focusable: false,
					deletable: false,
					zIndex: 0,
				} satisfies Edge,
			];
		});
		return [...lines, ...treeEdges];
	}, [dependencyLinks, treeEdges, layout, mode]);

	if (all ? visible.length === 0 : !project) {
		return (
			<Box sx={{ p: 2 }} data-testid={mindmapTestIds.page}>
				<Typography color="text.secondary" data-testid={mindmapTestIds.chooseProject}>
					{t(all ? "page.chooseProjects" : "page.chooseProject")}
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
						const title = id === rootId ? rootTitle : (nodes.find((node) => node.uid === id)?.title ?? "");
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
								key={`${view}:${projectUids.join(",")}:${freeTree ?? ""}`}
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
					{showUnassigned && !freeTree && (!all || unassignedProject) && <UnassignedPanel items={unassigned} />}
				</Box>
			</MapActionsContext.Provider>
			{deleteDialog}
			{menu && nodeOf(menu.id) && (
				<NodeMenu
					anchor={menu.anchor}
					shared={nodeOf(menu.id)!.tree_count > 1}
					onClose={() => setMenu(undefined)}
					onMove={() => setBranch({ source: sourceOf(nodeOf(menu.id)!), action: "move" })}
					onTransfer={() => setBranch({ source: sourceOf(nodeOf(menu.id)!), action: "transfer" })}
					onRemoveHere={() => {
						const node = nodeOf(menu.id)!;
						setError(undefined);
						removeFromMap({ ref: node.uid, version: node.version, tree: node.tree_uid }).unwrap().catch((failure: unknown) => setError(errorMessage(failure, t("error.failed"))));
					}}
					onDelete={() => actions.remove(menu.id)}
				/>
			)}
			{branch && <BranchDialog source={branch.source} action={branch.action} onClose={() => setBranch(undefined)} />}
			{trees && nodeOf(trees.id) && <TreeJumpMenu anchor={trees.anchor} node={trees.id} onClose={() => setTrees(undefined)} onPick={(tree) => jump(trees.id, tree)} />}
			{sharedDelete && nodeOf(sharedDelete) && (
				<DeleteSharedDialog node={sharedDelete} title={nodeOf(sharedDelete)!.title} version={nodeOf(sharedDelete)!.version} onClose={() => setSharedDelete(undefined)} onFail={setError} />
			)}
		</Box>
	);
}
