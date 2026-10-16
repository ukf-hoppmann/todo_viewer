import { Box } from "@mui/material";
import { ColorSchemeMenu } from "./ColorSchemeMenu";
import { LanguageSelect } from "./LanguageSelect";

/** The switches for the interface in an app bar, in one row (language, color scheme); shared by the app frame and the login page. */
export function AppBarControls() {
	return (
		<Box sx={{ display: "flex", alignItems: "center", flexShrink: 0, gap: 1, mx: 1 }}>
			<LanguageSelect />
			<ColorSchemeMenu />
		</Box>
	);
}
