import { Box } from "@mui/material";
import { LanguageSelect } from "./LanguageSelect";

/** The switches for the interface in an app bar, in one row (language); shared by the frames. */
export function AppBarControls() {
	return (
		<Box sx={{ display: "flex", alignItems: "center", flexShrink: 0, gap: 1, mx: 1 }}>
			<LanguageSelect />
		</Box>
	);
}
