import { describe, expect, it } from "vitest";
import { theme, ukfColors } from "../../../../../src/core/theme/theme";

/** The colors of the old application (`src_old/Redux/Styling/Theme.ts`), taken over unchanged. */
describe("ukfColors", () => {
	it("holds the UKF palette of the old application", () => {
		expect(ukfColors).toEqual({
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
		});
	});
});

/** `createTheme` types the color schemes only for the CSS-variables theme; they exist at runtime. */
type SchemePalette = { palette: Record<"primary" | "secondary" | "error" | "success", { main: string }> } | undefined;
const { light, dark } = (theme as unknown as { colorSchemes: { light: SchemePalette; dark: SchemePalette } }).colorSchemes;

describe("theme", () => {

	it("has a light and a dark color scheme", () => {
		expect(light).toBeDefined();
		expect(dark).toBeDefined();
	});

	it("uses the dark blue as primary color in the light scheme and the light blue in the dark scheme", () => {
		expect(light?.palette.primary.main).toBe("#004b96");
		expect(dark?.palette.primary.main).toBe("#28b4e6");
	});

	it("uses the red as secondary color in both schemes, the color of the selected sidebar entry", () => {
		expect(light?.palette.secondary.main).toBe("#be0028");
		expect(dark?.palette.secondary.main).toBe("#be0028");
	});

	it("uses the warm red for errors and the green for success in both schemes", () => {
		for (const scheme of [light, dark]) {
			expect(scheme?.palette.error.main).toBe("#e64641");
			expect(scheme?.palette.success.main).toBe("#73af55");
		}
	});
});
