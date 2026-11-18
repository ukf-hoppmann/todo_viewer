import { Box, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { LayoutMode } from "./mindmapLayout";
import { useMindmapState } from "./state";
import { mindmapTestIds } from "./testIds";

const LAYOUTS: readonly LayoutMode[] = ["side", "round"];

/** Sidebar section of the mind map: the arrangement of the map, the tree to the side or around the root. The choice is kept in the UI state. */
export function LayoutSwitch() {
	const { t } = useTranslation("mindmap");
	const { layout, setLayout } = useMindmapState();
	return (
		<Box data-testid={mindmapTestIds.layoutSwitch} component="section" aria-label={t("layout.title")}>
			<Typography variant="overline" color="text.secondary" component="h3">
				{t("layout.title")}
			</Typography>
			<ToggleButtonGroup
				exclusive
				fullWidth
				size="small"
				value={layout}
				aria-label={t("layout.title")}
				// Pressing the pressed button gives `null`: the choice stays.
				onChange={(_event, value: LayoutMode | null) => value && setLayout(value)}
			>
				{LAYOUTS.map((value) => (
					<ToggleButton key={value} value={value} data-testid={mindmapTestIds.layoutOption(value)}>
						{t(`layout.${value}`)}
					</ToggleButton>
				))}
			</ToggleButtonGroup>
		</Box>
	);
}
