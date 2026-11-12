import MemosIcon from "@mui/icons-material/StickyNote2";
import { definePlugin } from "../../core";
import { memosApi } from "./api";
import { CreateMemo, CreateTopic } from "./CreateForms";
import { MemosAttention } from "./MemosAttention";
import { MemoElementViewLoader } from "./elementView";
import { StatusFilter } from "./Filters";
import de from "./locales/de.json";
import en from "./locales/en.json";
import { ItemHints, DemoteAction } from "./ItemWidgets";
import { MemosSettings } from "./MemosSettings";

/**
 * Memos with a review date and their topics. The main route `memos/main` shows the tree per project (project →
 * topic → memo) and the detail of the selected memo; the status filter hangs in the sidebar of the core on that
 * route. Other plugins show a memo through `ElementDetail` of `workspace`. The due memos appear in the bell of the projects section (slot `workspace.attention-sources`), the review interval and the topic depth are in
 * the settings. Projects and the search text come from the plugin `workspace`. What the user chose (shown
 * statuses, folded nodes, the selected memo) is kept in the UI state of the server under the owner `memos`.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	api: memosApi,
	eventHandlers: {
		"memos.memo.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Memos", "Due"]));
		},
		// The server announces that a review date or a topic date has come (memos become due with the clock).
		"memos.due": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Memos", "Due"]));
		},
		"memos.topic.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Memos", "Due"]));
		},
		"memos.document.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Memos", "Documents"]));
		},
		"memos.settings.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Settings", "Memos", "Due"]));
		},
		"workspace.element.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Memos", "Due"]));
		},
		"core.reconnected": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Memos", "Due", "Documents", "Settings"]));
		},
	},
	contributions: [
		{ slot: "core.main", name: "main", title: "tab.memos", icon: MemosIcon, page: () => import("./pages/MemosPage"), layout: { sidebar: true, detail: true } },
		{ slot: "workspace.element-detail", name: "memo", component: MemoElementViewLoader },
		{ slot: "workspace.create-types", name: "memo", component: CreateMemo, order: 20 },
		{ slot: "workspace.create-types", name: "topic", component: CreateTopic, order: 21 },
		{ slot: "backlog.item-detail", name: "hints", component: ItemHints, order: 0 },
		{ slot: "backlog.item-detail", name: "demote", component: DemoteAction, order: 1 },
		{ slot: "core.sidebar-sections", name: "status-filter", component: StatusFilter, order: 20, when: ["memos/main"] },
		{ slot: "workspace.attention-sources", name: "due", component: MemosAttention },
		{ slot: "core.settings-sections", name: "settings", component: MemosSettings, order: 10, group: "system" },
	],
});

export { memosTestIds } from "./testIds";
