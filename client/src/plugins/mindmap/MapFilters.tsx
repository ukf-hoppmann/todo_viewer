import { Box, Checkbox, FormControlLabel } from "@mui/material";
import { useTranslation } from "react-i18next";
import { FilterSection } from "../../shared";
import { NODE_MARKS, NODE_STATES } from "./domain/tree";
import { useMindmapState } from "./state";
import { mindmapTestIds } from "./testIds";

const MARK_COLORS: Record<string, string> = { discarded: "#d5544a", later: "#4a7fd5" };
const STATE_COLORS: Record<string, string> = { idea: "#8a8f98", planned: "#6b7280", in_progress: "#d59a3a", done: "#3ab26b" };

/** Sidebar section of the mind map: which node states and marks are shown, and the switch of the side view "Nicht zugeordnet". */
export function MapFilters() {
	const { t } = useTranslation("mindmap");
	const { hiddenStates, setHiddenStates, hiddenMarks, setHiddenMarks, showUnassigned, setShowUnassigned } = useMindmapState();
	return (
		<Box data-testid={mindmapTestIds.stateFilter}>
			<FilterSection
				title={t("filter.state")}
				options={NODE_STATES.map((value) => ({ value, label: t(`state.${value}`), color: STATE_COLORS[value] }))}
				selected={NODE_STATES.filter((value) => !hiddenStates.includes(value))}
				onChange={(shown) => setHiddenStates(NODE_STATES.filter((value) => !shown.includes(value)))}
			/>
			<FilterSection
				title={t("filter.mark")}
				options={NODE_MARKS.map((value) => ({ value, label: t(`mark.${value}`), color: MARK_COLORS[value] }))}
				selected={NODE_MARKS.filter((value) => !hiddenMarks.includes(value))}
				onChange={(shown) => setHiddenMarks(NODE_MARKS.filter((value) => !shown.includes(value)))}
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
