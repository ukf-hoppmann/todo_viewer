import MindmapIcon from "@mui/icons-material/AccountTree";
import { definePlugin } from "../../core";
import { StatusFilter } from "../backlog";
import { mindmapApi } from "./api";
import de from "./locales/de.json";
import en from "./locales/en.json";
import { ItemNodeSection } from "./ItemNodeSection";
import { LayoutSwitch } from "./LayoutSwitch";
import { MapFilters } from "./MapFilters";

/**
 * The mind map: a topic tree per project to collect and order topics, independent of the backlog. The main route
 * `mindmap/main` shows the tree of one project (the marked one, else the only visible one; the projects come from
 * the plugin `workspace`) to the side, with the project as the root; nodes are added, renamed, folded and moved to
 * the trash in the map, title, text and documents (notes, specs) are edited in the detail column. What the user folded and the selected node
 * are kept in the UI state of the server under the owner `mindmap`. A node shows the count and progress of its items
 * (with its sub-nodes) and its state; the sidebar filters the nodes by state and shows the status filter of the
 * backlog, by which the server counts. The view can start at a node (the focus, `?focus=<uid>` in the address, with the
 * path back above the map); the detail of an item offers "Gehe hin", "Erstelle" and "Anker". A sidebar section switches the
 * arrangement of the map (`layout` in the UI state: the tree to the side, or around the root).
 */
export const plugin = definePlugin({
	i18n: { de, en },
	api: mindmapApi,
	eventHandlers: {
		"mindmap.node.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Tree", "Content", "ItemNode"]));
		},
		// A status change moves the counts, a changed memo its title in the detail of a node.
		"backlog.item.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Tree", "Content", "ItemNode"]));
		},
		"memos.memo.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Content"]));
		},
		"mindmap.document.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Tree", "Documents"]));
		},
		"workspace.element.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Tree", "Content", "ItemNode"]));
		},
		"core.reconnected": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Tree", "Documents", "Content", "ItemNode"]));
		},
	},
	contributions: [{ slot: "core.main", name: "main", title: "tab.mindmap", icon: MindmapIcon, page: () => import("./pages/MindmapPage"), layout: { sidebar: true, detail: true } },
		{ slot: "backlog.item-detail", name: "node", component: ItemNodeSection, order: 5 },
		{ slot: "core.sidebar-sections", name: "layout", component: LayoutSwitch, order: 19, when: ["mindmap/main"] },
		{ slot: "core.sidebar-sections", name: "state-filter", component: MapFilters, order: 20, when: ["mindmap/main"] },
		{ slot: "core.sidebar-sections", name: "status-filter", component: StatusFilter, order: 21, when: ["mindmap/main"] },
	],
});

export { mindmapTestIds } from "./testIds";
