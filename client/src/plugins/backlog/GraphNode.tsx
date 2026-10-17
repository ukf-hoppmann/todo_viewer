import { Box, Typography } from "@mui/material";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { memo } from "react";
import { ProgressRing } from "../../shared";
import type { IndexItem } from "./api";
import { priorityColor, statusColor } from "./constants";
import { backlogTestIds } from "./testIds";

export type GraphNodeData = { item: IndexItem; selected: boolean; dimmed: boolean };
export type ItemNode = Node<GraphNodeData, "item">;

const TITLE_LIMIT = 28;

/** A node of the dependency graph: priority dot, label, progress ring and the title; the border has the status color. */
export const GraphNode = memo(function GraphNode({ data }: NodeProps<ItemNode>) {
	const { item, selected, dimmed } = data;
	const title = item.title.length > TITLE_LIMIT ? `${item.title.slice(0, TITLE_LIMIT)}…` : item.title;
	return (
		<Box
			title={item.title}
			data-testid={backlogTestIds.graphNode(item.uid)}
			data-selected={selected}
			data-dimmed={dimmed}
			sx={{
				width: 200,
				height: 50,
				px: 1,
				py: 0.5,
				borderRadius: 1,
				border: "2px solid",
				borderColor: statusColor(item.status),
				bgcolor: selected ? "action.selected" : "background.paper",
				opacity: dimmed ? 0.25 : 1,
				cursor: "pointer",
				overflow: "hidden",
			}}
		>
			<Handle type="target" position={Position.Left} />
			<Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
				<Box sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: priorityColor(item.priority), flexShrink: 0 }} />
				<Typography variant="caption" sx={{ fontWeight: 600 }}>
					{item.label}
				</Typography>
				{item.progress && <ProgressRing done={item.progress.done} total={item.progress.total} />}
			</Box>
			<Typography variant="body2" noWrap>
				{title}
			</Typography>
			<Handle type="source" position={Position.Right} />
		</Box>
	);
});
