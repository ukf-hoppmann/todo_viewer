import { createTheme } from "@mui/material/styles";

/**
 * The colors of the old viewer (`src_old/web/src/styles.css`). Components never use these values
 * directly: they ask the theme (`background.default`, `primary.main`, …). Priority and status
 * colors belong to the plugins that show them.
 */
export const viewerColors = {
	background: "#0f1115",
	panel: "#171a21",
	panelBorder: "#262a33",
	surface: "#1c202a",
	hover: "#1f232c",
	selected: "#22304f",
	text: "#e6e8ec",
	textDim: "#9aa1ac",
	accent: "#5b8cff",
	success: "#3ab26b",
	warning: "#d59a3a",
	error: "#d5544a",
} as const;

/** The MUI theme: dark only, in the colors of the old viewer. */
export const theme = createTheme({
	palette: {
		mode: "dark",
		primary: { main: viewerColors.accent },
		secondary: { main: viewerColors.selected },
		error: { main: viewerColors.error },
		warning: { main: viewerColors.warning },
		success: { main: viewerColors.success },
		background: { default: viewerColors.background, paper: viewerColors.panel },
		text: { primary: viewerColors.text, secondary: viewerColors.textDim },
		divider: viewerColors.panelBorder,
		action: { hover: viewerColors.hover, selected: viewerColors.selected },
	},
	typography: { fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif', fontSize: 13 },
	components: {
		MuiAppBar: { styleOverrides: { root: { backgroundColor: viewerColors.panel, backgroundImage: "none" } } },
		MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
	},
});
