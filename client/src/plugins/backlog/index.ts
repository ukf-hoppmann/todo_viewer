import AccountTreeIcon from "@mui/icons-material/AccountTree";
import HubIcon from "@mui/icons-material/Hub";
import { definePlugin } from "../../core";
import { backlogApi } from "./api";
import { CreateEpic, CreateStory, CreateTask } from "./CreateForms";
import { ItemElementViewLoader } from "./elementView";
import { PriorityFilter, StatusFilter } from "./Filters";
import de from "./locales/de.json";
import en from "./locales/en.json";

/**
 * Epics, stories and tasks. The main route `backlog/main` shows the tree per project with the progress of
 * every item and the detail panel of the selected one, `backlog/graph` the dependencies between the items as a graph; the filters for status and priority hang in the
 * sidebar of the core on those routes. Other plugins show an item through `ElementDetail` of `workspace`. Projects and the search text come from the plugin `workspace`.
 * What the user chose (hidden statuses and priorities, folded items, the selected item) is kept in the UI
 * state of the server under the owner `backlog`.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	api: backlogApi,
	slots: {
		"item-detail": {
			description:
				"Widgets in the detail panel of an item, below its fields (for example the notices and the action 'back to a note' of `notes`): the widget reads the item with `useItemDetail`.",
		},
	},
	eventHandlers: {
		"backlog.item.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Items"]));
		},
		"backlog.document.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Items", "Documents"]));
		},
		"workspace.element.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Items"]));
		},
		// A sync writes items and documents imported from the mirror files without sending `backlog.*.changed`.
		"core.sync.state": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Items", "Documents"]));
		},
		"core.reconnected": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Items", "Documents"]));
		},
	},
	contributions: [
		{ slot: "core.main", name: "main", title: "tab.backlog", icon: AccountTreeIcon, page: () => import("./pages/BacklogPage"), layout: { sidebar: true, detail: true } },
		{ slot: "core.main", name: "graph", title: "tab.graph", icon: HubIcon, page: () => import("./pages/GraphPage"), layout: { sidebar: true, detail: true } },
		{ slot: "workspace.element-detail", name: "epic", component: ItemElementViewLoader },
		{ slot: "workspace.element-detail", name: "story", component: ItemElementViewLoader },
		{ slot: "workspace.element-detail", name: "task", component: ItemElementViewLoader },
		{ slot: "workspace.create-types", name: "epic", component: CreateEpic, order: 10 },
		{ slot: "workspace.create-types", name: "story", component: CreateStory, order: 11 },
		{ slot: "workspace.create-types", name: "task", component: CreateTask, order: 12 },
		{ slot: "core.sidebar-sections", name: "status-filter", component: StatusFilter, order: 20, when: ["backlog/main", "backlog/graph"] },
		{ slot: "core.sidebar-sections", name: "priority-filter", component: PriorityFilter, order: 21, when: ["backlog/main", "backlog/graph"] },
	],
});

export type { ItemOut } from "./api";
export { useItemDetail } from "./itemDetailContext";
export { StatusFilter } from "./Filters";
export { shownStatusesParam, useShownStatuses } from "./state";
export { backlogTestIds } from "./testIds";
