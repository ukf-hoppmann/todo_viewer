import { Box, Checkbox, FormControlLabel } from "@mui/material";
import { useTranslation } from "react-i18next";
import { FilterSection } from "../../shared";
import { NODE_STATES } from "./domain/tree";
import { useMindmapState } from "./state";
import { mindmapTestIds } from "./testIds";

const STATE_COLORS: Record<string, string> = { idea: "#8a8f98", planned: "#6b7280", in_progress: "#d59a3a", done: "#3ab26b" };

/** Sidebar section of the mind map: which node states are shown, and the switch of the side view "Nicht zugeordnet". */
export function MapFilters() {
	const { t } = useTranslation("mindmap");
	const { hiddenStates, setHiddenStates, showUnassigned, setShowUnassigned } = useMindmapState();
	return (
		<Box data-testid={mindmapTestIds.stateFilter}>
			<FilterSection
				title={t("filter.state")}
				options={NODE_STATES.map((value) => ({ value, label: t(`state.${value}`), color: STATE_COLORS[value] }))}
				selected={NODE_STATES.filter((value) => !hiddenStates.includes(value))}
				onChange={(shown) => setHiddenStates(NODE_STATES.filter((value) => !shown.includes(value)))}
			/>
			<FormControlLabel
				control={
					<Checkbox
						size="small"
						checked={showUnassigned}
						onChange={(event) => setShowUnassigned(event.target.checked)}
						slotProps={{ input: { "data-testid": mindmapTestIds.unassignedSwitch } as never }}
					/>
				}
				label={t("filter.unassigned")}
			/>
		</Box>
	);
}
