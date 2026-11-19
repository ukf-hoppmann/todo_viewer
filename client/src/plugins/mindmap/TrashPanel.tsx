import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { TrashedNodeOut } from "./api";
import { useMapActions } from "./mapActions";
import { mindmapTestIds } from "./testIds";

/**
 * The side view "Papierkorb": the deleted branches that stood in the map shown, to the side of the map. A branch is
 * dragged onto a place of the map and is brought back there with its nodes; it leaves the list when the server has
 * restored it. A branch counts once, by its top node (`nodes` is its size in the trash).
 */
export function TrashPanel({ branches }: { branches: readonly TrashedNodeOut[] }) {
	const { t } = useTranslation("mindmap");
	const actions = useMapActions();
	return (
		<Box
			data-testid={mindmapTestIds.trash}
			sx={{ width: 220, flexShrink: 0, ml: 1, border: 1, borderColor: "divider", display: "flex", flexDirection: "column", minHeight: 0 }}
		>
			<Box sx={{ p: 1, borderBottom: 1, borderColor: "divider" }}>
				<Typography variant="subtitle2">
					{t("trash.title")} ({branches.length})
				</Typography>
				<Typography variant="caption" color="text.secondary">
					{branches.length === 0 ? t("trash.empty") : t("trash.hint")}
				</Typography>
			</Box>
			<Box component="ul" sx={{ m: 0, p: 0, listStyle: "none", overflowY: "auto", flexGrow: 1 }}>
				{branches.map((branch) => (
					<Box
						component="li"
						key={branch.uid}
						draggable
						data-testid={mindmapTestIds.trashEntry(branch.uid)}
						onDragStart={(event) => {
							event.dataTransfer.setData("text/plain", branch.uid);
							event.dataTransfer.effectAllowed = "move";
							actions.dragStartTrash(branch.uid);
						}}
						onDragEnd={() => actions.dragEnd()}
						title={`${branch.label} · ${t("trash.size", { count: branch.nodes })}`}
						sx={{ px: 1, py: 0.5, cursor: "grab", borderBottom: 1, borderColor: "divider", "&:hover": { bgcolor: "action.hover" } }}
					>
						<Typography variant="caption" color="text.secondary" component="div">
							{branch.label} · {t("trash.size", { count: branch.nodes })}
						</Typography>
						<Typography variant="body2" noWrap>
							{branch.title}
						</Typography>
					</Box>
				))}
			</Box>
		</Box>
	);
}
