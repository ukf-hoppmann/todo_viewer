import { definePlugin } from "../../core";
import { Frame } from "./Frame";
import de from "./locales/de.json";
import en from "./locales/en.json";

/**
 * The layout of the viewer: app bar with the tabs of the main routes, the language switch and the widgets of
 * `layout-header-sidebar.header-actions` (for example counters), and a sidebar with the sections of
 * `layout-header-sidebar.sidebar-sections`, each shown only on the main routes named in its `when`.
 * It contains no business logic. A plugin that hangs into these slots lists this plugin in `requires`.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	frame: Frame,
	slots: {
		"header-actions": { description: "Small components at the right end of the app bar, e.g. a counter." },
		"sidebar-sections": { description: "Sections of the sidebar; `when` names the main routes they belong to." },
	},
});

export { layoutTestIds } from "./testIds";
