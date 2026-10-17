import { describe, expect, it } from "vitest";
import { theme, viewerColors } from "../../../../../../client/src/core/theme/theme";

/** The colors of the old viewer (`src_old/web/src/styles.css`). */
describe("theme", () => {
	it("is dark only", () => {
		expect(theme.palette.mode).toBe("dark");
	});

	it("takes background, text and accent from the old viewer", () => {
		expect(theme.palette.background.default).toBe(viewerColors.background);
		expect(theme.palette.background.paper).toBe(viewerColors.panel);
		expect(theme.palette.text.primary).toBe(viewerColors.text);
		expect(theme.palette.primary.main).toBe(viewerColors.accent);
	});

	it("uses the status colors of the old viewer for success, warning and error", () => {
		expect(theme.palette.success.main).toBe("#3ab26b");
		expect(theme.palette.warning.main).toBe("#d59a3a");
		expect(theme.palette.error.main).toBe("#d5544a");
	});
});
