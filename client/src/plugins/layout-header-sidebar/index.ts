import { definePlugin } from "../../core";
import { Frame } from "./Frame";
import de from "./locales/de.json";
import en from "./locales/en.json";

/**
 * The frame of the viewer: app bar with the tabs of the main routes, the language switch and the widgets of
 * `layout-header-sidebar.header-actions` (for example counters). The sidebar and the detail column are areas of
 * the core's sub layout that each main route switches on (`layout.sidebar`, `layout.detail`); sections of the
 * sidebar hang into `core.sidebar-sections`. It contains no business logic. A plugin that hangs into its slot
 * lists this plugin in `requires`.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	frame: Frame,
	slots: {
		"header-actions": { description: "Small components at the right end of the app bar, e.g. a counter." },
	},
});

export { layoutTestIds } from "./testIds";
