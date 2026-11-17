import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { ItemRefOut } from "./api";
import { useMapActions } from "./mapActions";
import { mindmapTestIds } from "./testIds";

/**
 * The side view "Nicht zugeordnet": the items without a node, to the side of the map. It is no node and does not
 * count in the tree. An item is dragged onto a node of the map to assign it; it leaves the list when the server
 * has assigned it.
 */
export function UnassignedPanel({ items }: { items: readonly ItemRefOut[] }) {
	const { t } = useTranslation("mindmap");
	const actions = useMapActions();
	return (
		<Box
			data-testid={mindmapTestIds.unassigned}
			sx={{ width: 260, flexShrink: 0, ml: 1, border: 1, borderColor: "divider", display: "flex", flexDirection: "column", minHeight: 0 }}
		>
			<Box sx={{ p: 1, borderBottom: 1, borderColor: "divider" }}>
				<Typography variant="subtitle2">
					{t("unassigned.title")} ({items.length})
				</Typography>
				<Typography variant="caption" color="text.secondary">
					{items.length === 0 ? t("unassigned.empty") : t("unassigned.hint")}
				</Typography>
			</Box>
			<Box component="ul" sx={{ m: 0, p: 0, listStyle: "none", overflowY: "auto", flexGrow: 1 }}>
				{items.map((item) => (
					<Box
						component="li"
						key={item.uid}
						draggable
						data-testid={mindmapTestIds.unassignedItem(item.uid)}
						onDragStart={(event) => {
							event.dataTransfer.setData("text/plain", item.uid);
							event.dataTransfer.effectAllowed = "move";
							actions.dragStartItem(item.uid);
						}}
						onDragEnd={() => actions.dragEnd()}
						title={`${item.label} · ${item.status}`}
						sx={{ px: 1, py: 0.5, cursor: "grab", borderBottom: 1, borderColor: "divider", "&:hover": { bgcolor: "action.hover" } }}
					>
						<Typography variant="caption" color="text.secondary" component="div">
							{item.label} · {item.status}
						</Typography>
						<Typography variant="body2" noWrap>
							{item.title}
						</Typography>
					</Box>
				))}
			</Box>
		</Box>
	);
}
