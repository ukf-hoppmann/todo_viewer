import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Box, IconButton, Typography } from "@mui/material";
import { useMemo, useRef, useState, type DragEvent, type KeyboardEvent, type ReactNode } from "react";
import { ProgressRing } from "../ProgressRing";
import { sharedTestIds } from "../testIds";
import { dropPosition, flattenVisible, isInSubtree, type DropPosition, type TreeNode } from "./treeModel";

export interface TreeDrop {
	sourceId: string;
	targetId: string;
	position: DropPosition;
}

interface TreeViewProps {
	/** The root nodes with their children. */
	nodes: readonly TreeNode[];
	/** Open nodes; the caller keeps them (usually with `usePersistentState`). */
	expanded: ReadonlySet<string>;
	onToggle: (id: string) => void;
	selectedId?: string | null;
	onSelect: (id: string) => void;
	/** Buttons shown at the right of a row while the pointer or the focus is on it. */
	actions?: (node: TreeNode) => ReactNode;
	/** Whether `source` may be dropped before, after, or into `target`; without it nothing can be dragged. */
	canDrop?: (source: TreeNode, target: TreeNode, position: DropPosition) => boolean;
	onDrop?: (drop: TreeDrop) => void;
	ariaLabel: string;
}

/**
 * A tree with selection, keyboard control and drag and drop. It holds no state of its own except the
 * focused row and the drag in progress; which nodes are open and which is selected belongs to the caller.
 * Keys: arrow down/up move, arrow right opens or goes to the first child, arrow left closes or goes to the
 * parent, Home/End jump, Enter or Space select.
 */
export function TreeView({ nodes, expanded, onToggle, selectedId, onSelect, actions, canDrop, onDrop, ariaLabel }: TreeViewProps) {
	const rows = useMemo(() => flattenVisible(nodes, expanded), [nodes, expanded]);
	const [focusId, setFocusId] = useState<string | undefined>();
	const [dragId, setDragId] = useState<string | undefined>();
	const [over, setOver] = useState<{ id: string; position: DropPosition } | undefined>();
	const refs = useRef(new Map<string, HTMLElement>());
	const parentOf = useMemo(() => {
		const map = new Map<string, string>();
		const walk = (list: readonly TreeNode[], parent?: string) => {
			for (const node of list) {
				if (parent) map.set(node.id, parent);
				walk(node.children, node.id);
			}
		};
		walk(nodes);
		return map;
	}, [nodes]);
	const byId = useMemo(() => new Map(rows.map((row) => [row.node.id, row.node])), [rows]);

	const tabStop = rows.find((row) => row.node.id === focusId) ? focusId : (rows.find((row) => row.node.id === selectedId)?.node.id ?? rows[0]?.node.id);
	const focus = (id: string | undefined) => {
		if (!id) return;
		setFocusId(id);
		refs.current.get(id)?.focus();
	};

	const onKeyDown = (event: KeyboardEvent, index: number) => {
		const row = rows[index]!;
		const { node } = row;
		switch (event.key) {
			case "ArrowDown":
				focus(rows[index + 1]?.node.id);
				break;
			case "ArrowUp":
				focus(rows[index - 1]?.node.id);
				break;
			case "Home":
				focus(rows[0]?.node.id);
				break;
			case "End":
				focus(rows.at(-1)?.node.id);
				break;
			case "ArrowRight":
				if (node.children.length === 0) return;
				if (!row.expanded) onToggle(node.id);
				else focus(node.children[0]!.id);
				break;
			case "ArrowLeft":
				if (row.expanded) onToggle(node.id);
				else focus(parentOf.get(node.id));
				break;
			case "Enter":
			case " ":
				onSelect(node.id);
				break;
			default:
				return;
		}
		event.preventDefault();
	};

	const dragEnabled = Boolean(canDrop && onDrop);
	const target = (event: DragEvent, node: TreeNode) => {
		const source = dragId ? byId.get(dragId) : undefined;
		if (!source || !canDrop) return undefined;
		const box = event.currentTarget.getBoundingClientRect();
		const position = dropPosition(event.clientY - box.top, box.height);
		if (isInSubtree(nodes, source.id, node.id) && position === "inside") return undefined;
		return canDrop(source, node, position) ? position : undefined;
	};

	return (
		<Box role="tree" aria-label={ariaLabel} data-testid={sharedTestIds.tree} sx={{ py: 0.5 }}>
			{rows.map(({ node, depth, expanded: open }, index) => {
				const selected = node.id === selectedId;
				const marker = over?.id === node.id ? over.position : undefined;
				return (
					<Box
						key={node.id}
						role="treeitem"
						aria-level={depth + 1}
						aria-selected={selected}
						aria-expanded={node.children.length > 0 ? open : undefined}
						tabIndex={node.id === tabStop ? 0 : -1}
						ref={(element: HTMLElement | null) => {
							if (element) refs.current.set(node.id, element);
							else refs.current.delete(node.id);
						}}
						data-testid={sharedTestIds.treeNode(node.id)}
						data-dashed={node.dashed ? "true" : undefined}
						data-area={node.area}
						draggable={dragEnabled}
						onClick={() => onSelect(node.id)}
						onFocus={() => setFocusId(node.id)}
						onKeyDown={(event) => onKeyDown(event, index)}
						onDragStart={(event) => {
							event.dataTransfer.effectAllowed = "move";
							event.dataTransfer.setData("text/plain", node.id);
							setDragId(node.id);
						}}
						onDragEnd={() => {
							setDragId(undefined);
							setOver(undefined);
						}}
						onDragOver={(event) => {
							const position = target(event, node);
							if (!position) {
								setOver(undefined);
								return;
							}
							event.preventDefault();
							event.dataTransfer.dropEffect = "move";
							setOver({ id: node.id, position });
						}}
						onDragLeave={() => setOver((current) => (current?.id === node.id ? undefined : current))}
						onDrop={(event) => {
							const position = target(event, node);
							const sourceId = dragId;
							setDragId(undefined);
							setOver(undefined);
							if (!position || !sourceId) return;
							event.preventDefault();
							onDrop?.({ sourceId, targetId: node.id, position });
						}}
						sx={{
							position: "relative",
							display: "flex",
							alignItems: "center",
							gap: 0.5,
							pl: depth * 2 + 0.5,
							pr: 1,
							minHeight: 32,
							cursor: "pointer",
							outline: "none",
							bgcolor: selected ? "action.selected" : node.area === 1 ? "action.hover" : "transparent",
							opacity: dragId === node.id ? 0.5 : node.dashed ? 0.7 : 1,
							border: node.dashed ? "1px dashed" : "1px solid transparent",
							borderColor: node.dashed ? "text.disabled" : "transparent",
							...(node.area ? { borderLeft: "3px solid", borderLeftColor: node.area === 1 ? "primary.main" : "text.disabled" } : {}),
							boxShadow: marker === "inside" ? (theme) => `inset 0 0 0 2px ${theme.palette.primary.main}` : "none",
							"&:hover, &:focus-visible": { bgcolor: selected ? "action.selected" : "action.hover" },
							"&:focus-visible": { outline: (theme) => `1px solid ${theme.palette.primary.main}` },
							"& .tree-actions": { visibility: "hidden" },
							"&:hover .tree-actions, &:focus-within .tree-actions": { visibility: "visible" },
						}}
					>
						{marker === "before" && <DropLine id={node.id} position="before" />}
						{marker === "after" && <DropLine id={node.id} position="after" />}
						{node.children.length > 0 ? (
							<IconButton
								size="small"
								tabIndex={-1}
								aria-hidden
								data-testid={sharedTestIds.treeToggle(node.id)}
								onClick={(event) => {
									event.stopPropagation();
									onToggle(node.id);
								}}
							>
								{open ? <ExpandMoreIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
							</IconButton>
						) : (
							<Box sx={{ width: 28, flexShrink: 0 }} />
						)}
						{node.tag && (
							<Typography
								variant="body2"
								data-testid={sharedTestIds.treeTag(node.id)}
								sx={{ flexShrink: 0, px: 0.5, borderRadius: 0.5, border: 1, borderColor: node.tagColor ?? "divider", color: node.tagColor ?? "text.secondary" }}
							>
								{node.tag}
							</Typography>
						)}
						{node.statusColor && <Box sx={{ width: 10, height: 10, borderRadius: "50%", bgcolor: node.statusColor, flexShrink: 0 }} />}
						{node.badge && (
							<Typography variant="caption" color="text.secondary" sx={{ flexShrink: 0 }}>
								{node.badge}
							</Typography>
						)}
						<Typography variant="body1" noWrap sx={{ flexGrow: 1, minWidth: 0, fontSize: "1.1rem" }}>
							{node.label}
						</Typography>
						{node.progress && <ProgressRing done={node.progress.done} total={node.progress.total} />}
						{node.count !== undefined && (
							<Typography variant="caption" color="text.secondary" data-testid={sharedTestIds.treeCount(node.id)} sx={{ flexShrink: 0 }}>
								{node.count}
							</Typography>
						)}
						{actions && (
							<Box className="tree-actions" data-testid={sharedTestIds.treeActions(node.id)} onClick={(event) => event.stopPropagation()} sx={{ display: "flex" }}>
								{actions(node)}
							</Box>
						)}
					</Box>
				);
			})}
		</Box>
	);
}

function DropLine({ id, position }: { id: string; position: "before" | "after" }) {
	return (
		<Box
			data-testid={sharedTestIds.treeDrop(id, position)}
			sx={{ position: "absolute", left: 0, right: 0, height: 2, bgcolor: "primary.main", [position === "before" ? "top" : "bottom"]: 0 }}
		/>
	);
}
