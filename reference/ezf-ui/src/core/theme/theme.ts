import { createTheme } from "@mui/material/styles";

/**
 * The UKF colors, taken over unchanged from the old application
 * (`src_old/Redux/Styling/Theme.ts`). Components never use these values
 * directly: they ask the theme (`primary.main`, `secondary.main`, …).
 */
export const ukfColors = {
	primaryRed: "#be0028",
	primaryBlue: "#004b96",
	primaryGrey: "#c8c8c8",
	secondaryYellow: "#f5af32",
	secondaryBlue: "#28b4e6",
	secondaryBlueGreen: "#00aaaa",
	secondaryLightPurple: "#8782a5",
	secondaryGrey: "#aabec8",
	secondaryRed: "#aa4b5a",
	secondaryGreen: "#73af55",
	secondaryWarmRed: "#e64641",
} as const;

/** The MUI theme with a light and a dark color scheme in the UKF colors. */
export const theme = createTheme({
	components: {
		// The app bar stays black in the dark scheme so the sub header can stand out from it.
		MuiAppBar: {
			styleOverrides: {
				root: ({ theme }) =>
					theme.applyStyles("dark", {
						backgroundColor: "#000",
						backgroundImage: "none",
					}),
			},
		},
	},
	colorSchemes: {
		dark: {
			palette: {
				primary: { main: ukfColors.secondaryBlue },
				secondary: { main: ukfColors.primaryRed },
				error: { main: ukfColors.secondaryWarmRed },
				success: { main: ukfColors.secondaryGreen },
			},
		},
		light: {
			palette: {
				primary: { main: ukfColors.primaryBlue },
				secondary: { main: ukfColors.primaryRed },
				error: { main: ukfColors.secondaryWarmRed },
				success: { main: ukfColors.secondaryGreen },
			},
		},
	},
});
