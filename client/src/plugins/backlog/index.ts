import AccountTreeIcon from "@mui/icons-material/AccountTree";
import { definePlugin } from "../../core";
import { backlogApi } from "./api";
import { CreateEpic, CreateStory, CreateTask } from "./CreateForms";
import { PriorityFilter, StatusFilter } from "./Filters";
import de from "./locales/de.json";
import en from "./locales/en.json";

/**
 * Epics, stories and tasks. The main route `backlog/main` shows the tree per project with the progress of
 * every item and the detail panel of the selected one; the filters for status and priority hang in the
 * sidebar of the layout plugin on that route. Projects and the search text come from the plugin `workspace`.
 * What the user chose (hidden statuses and priorities, folded items, the selected item) is kept in the UI
 * state of the server under the owner `backlog`.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	api: backlogApi,
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
		"core.reconnected": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Items", "Documents"]));
		},
	},
	contributions: [
		{ slot: "core.main", name: "main", title: "tab.backlog", icon: AccountTreeIcon, page: () => import("./pages/BacklogPage") },
		{ slot: "workspace.create-types", name: "epic", component: CreateEpic, order: 10 },
		{ slot: "workspace.create-types", name: "story", component: CreateStory, order: 11 },
		{ slot: "workspace.create-types", name: "task", component: CreateTask, order: 12 },
		{ slot: "layout-header-sidebar.sidebar-sections", name: "status-filter", component: StatusFilter, order: 20, when: ["backlog/main"] },
		{ slot: "layout-header-sidebar.sidebar-sections", name: "priority-filter", component: PriorityFilter, order: 21, when: ["backlog/main"] },
	],
});

export { backlogTestIds } from "./testIds";
