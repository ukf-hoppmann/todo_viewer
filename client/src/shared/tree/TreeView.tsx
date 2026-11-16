import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Box, IconButton, Typography } from "@mui/material";
import { memo, useCallback, useEffect, useMemo, useRef, useState, type DragEvent, type KeyboardEvent, type ReactNode } from "react";
import { ProgressRing } from "../ProgressRing";
import { sharedTestIds } from "../testIds";
import { dropPosition, flattenVisible, guideLines, isInSubtree, type DropPosition, type TreeNode } from "./treeModel";

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
	/**
	 * Something shown at the right of the label while the pointer or the focus is on the row, e.g. a small symbol with a tooltip.
	 * Keep the function (and `actions`) the same between renders (`useCallback`) so that a row is only drawn again when it changes.
	 */
	trailing?: (node: TreeNode) => ReactNode;
	/** Buttons shown at the right of a row while the pointer or the focus is on it. */
	actions?: (node: TreeNode) => ReactNode;
	/** Whether `source` may be dropped before, after, or into `target`; without it nothing can be dragged. */
	canDrop?: (source: TreeNode, target: TreeNode, position: DropPosition) => boolean;
	onDrop?: (drop: TreeDrop) => void;
	ariaLabel: string;
}

/** The newest value in a ref, for handlers that must keep their identity (their callers often pass fresh functions). */
function useLatest<T>(value: T) {
	const ref = useRef(value);
	useEffect(() => {
		ref.current = value;
	});
	return ref;
}

/**
 * A tree with selection, keyboard control and drag and drop. It holds no state of its own except the
 * focused row and the drag in progress; which nodes are open and which is selected belongs to the caller.
 * Keys: arrow down/up move, arrow right opens or goes to the first child, arrow left closes or goes to the
 * parent, Home/End jump, Enter or Space select.
 *
 * Every row is a memoized component with stable handlers: choosing a row draws only the row that lost and the row
 * that got the selection, not the whole tree. This holds as long as `nodes` and `expanded` keep their identity
 * between renders (`useMemo`), and `trailing` and `actions` too.
 */
export function TreeView({ nodes, expanded, onToggle, selectedId, onSelect, trailing, actions, canDrop, onDrop, ariaLabel }: TreeViewProps) {
	const rows = useMemo(() => flattenVisible(nodes, expanded), [nodes, expanded]);
	const lines = useMemo(() => guideLines(rows), [rows]);
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

	// The callers' handlers are only called from events, so the newest ones are read at call time.
	const onToggleRef = useLatest(onToggle);
	const onSelectRef = useLatest(onSelect);
	const canDropRef = useLatest(canDrop);
	const onDropRef = useLatest(onDrop);
	const toggle = useCallback((id: string) => onToggleRef.current(id), [onToggleRef]);
	const select = useCallback((id: string) => onSelectRef.current(id), [onSelectRef]);

	const tabStop = rows.find((row) => row.node.id === focusId) ? focusId : (rows.find((row) => row.node.id === selectedId)?.node.id ?? rows[0]?.node.id);
	const register = useCallback((id: string, element: HTMLElement | null) => {
		if (element) refs.current.set(id, element);
		else refs.current.delete(id);
	}, []);
	const focus = useCallback((id: string | undefined) => {
		if (!id) return;
		setFocusId(id);
		refs.current.get(id)?.focus();
	}, []);

	const onKeyDown = useCallback(
		(event: KeyboardEvent, index: number) => {
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
					if (!row.expanded) toggle(node.id);
					else focus(node.children[0]!.id);
					break;
				case "ArrowLeft":
					if (row.expanded) toggle(node.id);
					else focus(parentOf.get(node.id));
					break;
				case "Enter":
				case " ":
					select(node.id);
					break;
				default:
					return;
			}
			event.preventDefault();
		},
		[rows, parentOf, focus, toggle, select],
	);

	const dragEnabled = Boolean(canDrop && onDrop);
	const target = useCallback(
		(event: DragEvent, node: TreeNode) => {
			const source = dragId ? byId.get(dragId) : undefined;
			const allowed = canDropRef.current;
			if (!source || !allowed) return undefined;
			const box = event.currentTarget.getBoundingClientRect();
			const position = dropPosition(event.clientY - box.top, box.height);
			if (isInSubtree(nodes, source.id, node.id) && position === "inside") return undefined;
			return allowed(source, node, position) ? position : undefined;
		},
		[dragId, byId, nodes, canDropRef],
	);

	const onDragStart = useCallback((event: DragEvent, id: string) => {
		event.dataTransfer.effectAllowed = "move";
		event.dataTransfer.setData("text/plain", id);
		setDragId(id);
	}, []);
	const onDragEnd = useCallback(() => {
		setDragId(undefined);
		setOver(undefined);
	}, []);
	const onDragOver = useCallback(
		(event: DragEvent, node: TreeNode) => {
			const position = target(event, node);
			if (!position) {
				setOver(undefined);
				return;
			}
			event.preventDefault();
			event.dataTransfer.dropEffect = "move";
			// dragover fires continuously; keep the state object while nothing changed so that nothing is drawn again.
			setOver((current) => (current?.id === node.id && current.position === position ? current : { id: node.id, position }));
		},
		[target],
	);
	const onDragLeave = useCallback((id: string) => setOver((current) => (current?.id === id ? undefined : current)), []);
	const onRowDrop = useCallback(
		(event: DragEvent, node: TreeNode) => {
			const position = target(event, node);
			const sourceId = dragId;
			setDragId(undefined);
			setOver(undefined);
			if (!position || !sourceId) return;
			event.preventDefault();
			onDropRef.current?.({ sourceId, targetId: node.id, position });
		},
		[target, dragId, onDropRef],
	);

	return (
		<Box role="tree" aria-label={ariaLabel} data-testid={sharedTestIds.tree} sx={{ py: 0.5 }}>
			{rows.map(({ node, depth, expanded: open }, index) => (
				<TreeRow
					key={node.id}
					node={node}
					depth={depth}
					index={index}
					open={open}
					guides={lines[index]!}
					selected={node.id === selectedId}
					tabStop={node.id === tabStop}
					marker={over?.id === node.id ? over.position : undefined}
					dragging={dragId === node.id}
					dragEnabled={dragEnabled}
					trailing={trailing}
					actions={actions}
					register={register}
					onSelect={select}
					onToggle={toggle}
					onFocusRow={setFocusId}
					onKeyDown={onKeyDown}
					onDragStart={onDragStart}
					onDragEnd={onDragEnd}
					onDragOver={onDragOver}
					onDragLeave={onDragLeave}
					onDrop={onRowDrop}
				/>
			))}
		</Box>
	);
}

interface TreeRowProps {
	node: TreeNode;
	depth: number;
	index: number;
	open: boolean;
	guides: readonly boolean[];
	selected: boolean;
	tabStop: boolean;
	marker: DropPosition | undefined;
	dragging: boolean;
	dragEnabled: boolean;
	trailing: ((node: TreeNode) => ReactNode) | undefined;
	actions: ((node: TreeNode) => ReactNode) | undefined;
	register: (id: string, element: HTMLElement | null) => void;
	onSelect: (id: string) => void;
	onToggle: (id: string) => void;
	onFocusRow: (id: string) => void;
	onKeyDown: (event: KeyboardEvent, index: number) => void;
	onDragStart: (event: DragEvent, id: string) => void;
	onDragEnd: () => void;
	onDragOver: (event: DragEvent, node: TreeNode) => void;
	onDragLeave: (id: string) => void;
	onDrop: (event: DragEvent, node: TreeNode) => void;
}

/** One row. Memoized: with unchanged props it is not drawn again, which is what keeps a click in a long tree cheap. */
const TreeRow = memo(function TreeRow({
	node,
	depth,
	index,
	open,
	guides,
	selected,
	tabStop,
	marker,
	dragging,
	dragEnabled,
	trailing,
	actions,
	register,
	onSelect,
	onToggle,
	onFocusRow,
	onKeyDown,
	onDragStart,
	onDragEnd,
	onDragOver,
	onDragLeave,
	onDrop,
}: TreeRowProps) {
	const setRef = useCallback((element: HTMLElement | null) => register(node.id, element), [register, node.id]);
	return (
		<Box
			role="treeitem"
			aria-level={depth + 1}
			aria-selected={selected}
			aria-expanded={node.children.length > 0 ? open : undefined}
			tabIndex={tabStop ? 0 : -1}
			ref={setRef}
			data-testid={sharedTestIds.treeNode(node.id)}
			data-dashed={node.dashed ? "true" : undefined}
			data-area={node.area}
			draggable={dragEnabled}
			onClick={() => onSelect(node.id)}
			onFocus={() => onFocusRow(node.id)}
			onKeyDown={(event) => onKeyDown(event, index)}
			onDragStart={(event) => onDragStart(event, node.id)}
			onDragEnd={onDragEnd}
			onDragOver={(event) => onDragOver(event, node)}
			onDragLeave={() => onDragLeave(node.id)}
			onDrop={(event) => onDrop(event, node)}
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
				opacity: dragging ? 0.5 : 1,
				border: "1px solid transparent",
				...(node.area ? { borderLeft: "3px solid", borderLeftColor: node.area === 1 ? "primary.main" : "text.disabled" } : {}),
				boxShadow: marker === "inside" ? (theme) => `inset 0 0 0 2px ${theme.palette.primary.main}` : "none",
				"&:hover, &:focus-visible": { bgcolor: selected ? "action.selected" : "action.hover" },
				"&:focus-visible": { outline: (theme) => `1px solid ${theme.palette.primary.main}` },
				"& .tree-actions": { visibility: "hidden" },
				"&:hover .tree-actions, &:focus-within .tree-actions": { visibility: "visible" },
			}}
		>
			{guides.map((dashed, level) => (
				<Box
					key={level}
					aria-hidden
					data-guide={dashed ? "dashed" : "solid"}
					sx={{
						position: "absolute",
						top: 0,
						bottom: 0,
						left: `${level * 16 + 18}px`,
						borderLeft: "1px",
						borderLeftStyle: dashed ? "dashed" : "solid",
						borderLeftColor: dashed ? "action.disabled" : "divider",
					}}
				/>
			))}
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
			{node.statusColor && (
				<Box
					sx={{
						width: 10,
						height: 10,
						borderRadius: "50%",
						flexShrink: 0,
						boxSizing: "border-box",
						...(node.dashed ? { border: "1.5px solid", borderColor: node.statusColor } : { bgcolor: node.statusColor }),
					}}
				/>
			)}
			{node.badge && (
				<Typography variant="caption" sx={{ flexShrink: 0, color: node.badgeColor ?? "text.secondary", ...(node.badgeColor && { fontWeight: 600 }) }}>
					{node.badge}
				</Typography>
			)}
			<Typography variant="body1" noWrap color={node.dashed ? "text.secondary" : undefined} sx={{ flexGrow: 1, minWidth: 0, fontSize: "1.1rem" }}>
				{node.label}
			</Typography>
			{trailing && (
				<Box className="tree-actions" sx={{ display: "flex", alignItems: "center" }}>
					{trailing(node)}
				</Box>
			)}
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
});

function DropLine({ id, position }: { id: string; position: "before" | "after" }) {
	return (
		<Box
			data-testid={sharedTestIds.treeDrop(id, position)}
			sx={{ position: "absolute", left: 0, right: 0, height: 2, bgcolor: "primary.main", [position === "before" ? "top" : "bottom"]: 0 }}
		/>
	);
}
