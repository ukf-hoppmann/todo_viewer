import { Box, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { ViewMode } from "./domain/tree";
import { useMindmapState } from "./state";
import { mindmapTestIds } from "./testIds";

const LAYOUTS: readonly ViewMode[] = ["single", "all"];

/** Sidebar section of the mind map: the view of the map, one project or all chosen projects under a common root. The choice is kept in the UI state. */
export function ViewSwitch() {
	const { t } = useTranslation("mindmap");
	const { view, setView } = useMindmapState();
	return (
		<Box data-testid={mindmapTestIds.viewSwitch} component="section" aria-label={t("view.title")}>
			<Typography variant="overline" color="text.secondary" component="h3">
				{t("view.title")}
			</Typography>
			<ToggleButtonGroup
				exclusive
				fullWidth
				size="small"
				value={view}
				aria-label={t("view.title")}
				// Pressing the pressed button gives `null`: the choice stays.
				onChange={(_event, value: ViewMode | null) => value && setView(value)}
			>
				{LAYOUTS.map((value) => (
					<ToggleButton key={value} value={value} data-testid={mindmapTestIds.viewOption(value)}>
						{t(`view.${value}`)}
					</ToggleButton>
				))}
			</ToggleButtonGroup>
		</Box>
	);
}
