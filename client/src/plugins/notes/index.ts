import NotesIcon from "@mui/icons-material/StickyNote2";
import { definePlugin } from "../../core";
import { notesApi } from "./api";
import { CreateNote, CreateTopic } from "./CreateForms";
import { DueCounter } from "./DueCounter";
import { StatusFilter } from "./Filters";
import de from "./locales/de.json";
import en from "./locales/en.json";
import { ItemNotices, DemoteAction } from "./ItemWidgets";
import { NotesSettings } from "./NotesSettings";

/**
 * Notes with a review date and their topics. The main route `notes/main` shows the tree per project (project →
 * topic → note) and the detail of the selected note; the status filter hangs in the sidebar of the layout plugin
 * on that route. The number of due notes stands in the app bar, the review interval and the topic depth are in
 * the settings. Projects and the search text come from the plugin `workspace`. What the user chose (shown
 * statuses, folded nodes, the selected note) is kept in the UI state of the server under the owner `notes`.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	api: notesApi,
	eventHandlers: {
		"notes.note.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Notes", "Due"]));
		},
		"notes.topic.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Notes", "Due"]));
		},
		"notes.document.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Notes", "Documents"]));
		},
		"notes.settings.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Settings", "Notes", "Due"]));
		},
		"workspace.element.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Notes", "Due"]));
		},
		"core.reconnected": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Notes", "Due", "Documents", "Settings"]));
		},
	},
	contributions: [
		{ slot: "core.main", name: "main", title: "tab.notes", icon: NotesIcon, page: () => import("./pages/NotesPage"), layout: { sidebar: true, detail: true } },
		{ slot: "workspace.create-types", name: "note", component: CreateNote, order: 20 },
		{ slot: "workspace.create-types", name: "topic", component: CreateTopic, order: 21 },
		{ slot: "backlog.item-detail", name: "notices", component: ItemNotices, order: 0 },
		{ slot: "backlog.item-detail", name: "demote", component: DemoteAction, order: 1 },
		{ slot: "core.sidebar-sections", name: "status-filter", component: StatusFilter, order: 20, when: ["notes/main"] },
		{ slot: "layout-header-sidebar.header-actions", name: "due", component: DueCounter, order: 0 },
		{ slot: "core.settings-sections", name: "settings", component: NotesSettings, order: 10 },
	],
});

export { notesTestIds } from "./testIds";
