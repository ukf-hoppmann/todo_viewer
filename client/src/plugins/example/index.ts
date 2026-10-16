import AccountTreeIcon from "@mui/icons-material/AccountTree";
import ViewListIcon from "@mui/icons-material/ViewList";
import { definePlugin } from "../../core";
import { exampleApi } from "./api";
import { EventCounter } from "./EventCounter";
import de from "./locales/de.json";
import en from "./locales/en.json";
import { SettingsSection } from "./SettingsSection";
import { SidebarSection } from "./SidebarSection";
import { exampleEventSeen, exampleReducer } from "./state/eventsSlice";

/**
 * Minimal plugin without business logic, only in the development mode: the template for new plugins. A tab
 * (`overview`) whose page shows the status of the server from the own API, a counter in the own compartment
 * of the store, and a value in the UI state; widgets in the slots of the layout plugin and of the settings
 * page; and handlers for server events: on `core.sync.state` and after a reconnect it reloads its data
 * (it invalidates the tag `Health`). Texts are used with `useTranslation("example")`.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	reducer: exampleReducer,
	api: exampleApi,
	eventHandlers: {
		"core.sync.state": (_payload, { dispatch, api }) => {
			dispatch(exampleEventSeen());
			if (api?.util) dispatch(api.util.invalidateTags(["Health"]));
		},
		"core.reconnected": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Health"]));
		},
	},
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
			name: "workbench",
			title: "tab.workbench",
			icon: AccountTreeIcon,
			page: () => import("./pages/WorkbenchPage"),
		},
		{ slot: "layout-header-sidebar.header-actions", name: "event-counter", component: EventCounter },
		{ slot: "layout-header-sidebar.sidebar-sections", name: "info", component: SidebarSection, when: ["example/overview"] },
		{ slot: "core.settings-sections", name: "info", component: SettingsSection },
	],
});

export { exampleCountUp, selectExampleCount, selectExampleEvents } from "./state/eventsSlice";
export { exampleTestIds } from "./testIds";
