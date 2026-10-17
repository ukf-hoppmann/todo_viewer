import { Box } from "@mui/material";
import { useSlot } from "../../core";
import { DetailElementState, type DetailElement } from "./detailElement";

/**
 * The widgets that other plugins hang into every detail panel (for example "set an alarm" of `alarms`). Plugins with a
 * detail panel build this into it, next to `LinksSection`.
 */
export function DetailSections({ uid, label, projectUid }: DetailElement) {
	const widgets = useSlot("workspace.detail-sections");
	if (widgets.length === 0) return null;
	return (
		<DetailElementState.Provider value={{ uid, label, projectUid }}>
			<Box sx={{ display: "flex", flexDirection: "column", gap: 1 }} data-testid="workspace.detail-sections">
				{widgets.map((entry) => (
					<entry.component key={`${entry.ownerId}/${entry.name}`} />
				))}
			</Box>
		</DetailElementState.Provider>
	);
}
