import HomeIcon from "@mui/icons-material/Home";
import ViewListIcon from "@mui/icons-material/ViewList";
import ViewSidebarIcon from "@mui/icons-material/ViewSidebar";
import { definePlugin } from "../../core";
import { exampleApi } from "./api";
import de from "./locales/de.json";
import en from "./locales/en.json";
import { exampleReducer } from "./state/counterSlice";

/**
 * Minimal plugin without business logic: the template for new plugins. It
 * grows with the plugin contract. Texts are used with `useTranslation("example")`.
 * It contributes a tab whose page asks for a header area and fills it, and a
 * tab with a sidebar (slot `example.hub`) with one entry of its own; the
 * plugin `example-addon` hangs a second entry into that sidebar. Its page
 * `overview` has a counter in the plugin's own compartment of the store and
 * shows the version of the backend from the plugin's own API (`api.ts`, cache
 * under `example.api`); other plugins read the counter only through the
 * selector and the action exported here.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	reducer: exampleReducer,
	api: exampleApi,
	contributions: [
		{
			slot: "core.main",
			name: "overview",
			title: "tab.overview",
			icon: ViewListIcon,
			page: () => import("./pages/OverviewPage"),
			layout: { header: true },
		},
		{
			slot: "core.main",
			name: "hub",
			title: "tab.hub",
			icon: ViewSidebarIcon,
			layout: { header: true, sidebar: true },
		},
		{
			slot: "example.hub",
			name: "start",
			title: "entry.start",
			icon: HomeIcon,
			page: () => import("./pages/StartPage"),
		},
	],
});

export { exampleCountUp, selectExampleCount } from "./state/counterSlice";
export { exampleTestIds } from "./testIds";
