import AddIcon from "@mui/icons-material/Add";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import DeleteIcon from "@mui/icons-material/DeleteOutlined";
import { Box, InputBase, Typography } from "@mui/material";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { memo, useRef, type DragEvent } from "react";
import { useTranslation } from "react-i18next";
import { dropPosition, IconAction } from "../../shared";
import type { DropZone } from "./domain/tree";
import { useMapActions } from "./mapActions";
import { NODE_HEIGHT, NODE_WIDTH } from "./mindmapLayout";
import { mindmapTestIds } from "./testIds";

export type TopicData = { id: string; title: string; isRoot: boolean; hasChildren: boolean; open: boolean; selected: boolean; editing: boolean; dragging?: boolean; drop?: DropZone };
export type TopicNode = Node<TopicData, "topic">;

const HIDDEN_HANDLE = { opacity: 0, pointerEvents: "none" } as const;

/**
 * A node of the mind map: the title (an input while it is renamed), at the right edge the arrow that folds its
 * children, and above it, while pointer or focus are on the node, the actions "add child" and "trash". The root is
 * the project: it cannot be renamed or deleted. A node is dragged onto another one to move it with its branch: the
 * upper quarter of the target places it before, the lower quarter after, the middle below the target; the page says
 * whether a place is offered and marks it (`drop`).
 */
export const MindmapNode = memo(function MindmapNode({ data }: NodeProps<TopicNode>) {
	const { id, title, isRoot, hasChildren, open, selected, editing, dragging, drop } = data;
	const { t } = useTranslation("mindmap");
	const actions = useMapActions();
	// Esc ends the edit; the blur that follows must not save it.
	const cancelled = useRef(false);
	const zoneOf = (event: DragEvent<HTMLElement>): DropZone => {
		const box = event.currentTarget.getBoundingClientRect();
		return dropPosition(event.clientY - box.top, box.height);
	};
	return (
		<Box
			title={title}
			data-testid={mindmapTestIds.node(id)}
			data-selected={selected}
			data-drop={drop}
			className={isRoot ? undefined : "nodrag nopan"}
			draggable={!isRoot && !editing}
			onDragStart={(event) => {
				event.dataTransfer.setData("text/plain", id);
				event.dataTransfer.effectAllowed = "move";
				actions.dragStart(id);
			}}
			onDragEnd={() => actions.dragEnd()}
			onDragOver={(event) => {
				if (!actions.dragOver(id, zoneOf(event))) return;
				event.preventDefault();
				event.dataTransfer.dropEffect = "move";
			}}
			onDragLeave={() => actions.dragLeave(id)}
			onDrop={(event) => {
				event.preventDefault();
				actions.drop(id, zoneOf(event));
			}}
			onDoubleClick={isRoot ? undefined : () => actions.startRename(id)}
			sx={{
				position: "relative",
				width: NODE_WIDTH,
				height: NODE_HEIGHT,
				pl: 1.5,
				pr: 0.5,
				display: "flex",
				alignItems: "center",
				gap: 0.5,
				borderRadius: isRoot ? 1 : 4,
				border: "2px solid",
				borderColor: selected || isRoot || drop === "inside" ? "primary.main" : "divider",
				borderStyle: drop === "inside" ? "dashed" : "solid",
				bgcolor: selected || drop === "inside" ? "action.selected" : "background.paper",
				opacity: dragging ? 0.5 : 1,
				cursor: isRoot ? "default" : "pointer",
				"& .mindmap-node-actions": { visibility: "hidden" },
				"&:hover .mindmap-node-actions, &:focus-within .mindmap-node-actions": { visibility: "visible" },
			}}
		>
			{(drop === "before" || drop === "after") && (
				<Box
					data-testid={mindmapTestIds.dropLine(id, drop)}
					sx={{ position: "absolute", left: 0, right: 0, height: 3, borderRadius: 1, bgcolor: "primary.main", pointerEvents: "none", ...(drop === "before" ? { top: -8 } : { bottom: -8 }) }}
				/>
			)}
			{!isRoot && <Handle type="target" position={Position.Left} style={HIDDEN_HANDLE} />}
			{editing ? (
				<InputBase
					autoFocus
					fullWidth
					className="nodrag nopan"
					defaultValue={title}
					sx={{ fontSize: "0.875rem" }}
					onFocus={(event) => {
						cancelled.current = false;
						event.target.select();
					}}
					onClick={(event) => event.stopPropagation()}
					onDoubleClick={(event) => event.stopPropagation()}
					onKeyDown={(event) => {
						if (event.key === "Enter") actions.commitTitle(id, (event.target as HTMLInputElement).value);
						if (event.key === "Escape") {
							cancelled.current = true;
							actions.cancelRename();
						}
					}}
					onBlur={(event) => {
						if (!cancelled.current) actions.commitTitle(id, event.target.value);
					}}
					inputProps={{ "data-testid": mindmapTestIds.titleInput(id), "aria-label": t("field.title") }}
				/>
			) : (
				<Typography variant="body2" noWrap sx={{ flexGrow: 1, minWidth: 0, fontWeight: isRoot ? 600 : 400 }}>
					{title}
				</Typography>
			)}
			{hasChildren && !editing && (
				<Box className="nodrag nopan" sx={{ flexShrink: 0 }} onClick={(event) => event.stopPropagation()} onDoubleClick={(event) => event.stopPropagation()}>
					<IconAction
						label={t(open ? "action.collapse" : "action.expand")}
						icon={open ? ChevronLeftIcon : ChevronRightIcon}
						onClick={() => actions.toggle(id)}
						testId={mindmapTestIds.toggle(id)}
					/>
				</Box>
			)}
			{!editing && (
				<Box
					className="mindmap-node-actions nodrag nopan"
					onClick={(event) => event.stopPropagation()}
					onDoubleClick={(event) => event.stopPropagation()}
					sx={{ position: "absolute", right: 8, bottom: "100%", display: "flex", bgcolor: "background.paper", border: 1, borderBottom: 0, borderColor: "divider", borderRadius: "8px 8px 0 0" }}
				>
					<IconAction label={t("action.add")} icon={AddIcon} onClick={() => actions.add(id)} testId={mindmapTestIds.add(id)} />
					{!isRoot && <IconAction label={t("action.remove")} icon={DeleteIcon} onClick={() => actions.remove(id)} testId={mindmapTestIds.remove(id)} />}
				</Box>
			)}
			<Handle type="source" position={Position.Right} style={HIDDEN_HANDLE} />
		</Box>
	);
});
