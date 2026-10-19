import DeleteIcon from "@mui/icons-material/Delete";
import { definePlugin } from "../../core";
import { workspaceApi } from "./api";
import de from "./locales/de.json";
import en from "./locales/en.json";
import { NewButton } from "./NewButton";
import { ProjectSettings } from "./ProjectSettings";
import { ProjectsSection } from "./ProjectsSection";
import { SearchSection } from "./SearchSection";

/**
 * Projects, search and the "＋ New" dialog. Sections for the search and the projects hang in the sidebar of
 * the layout plugin, the button in its app bar. Other plugins read the public state through the hooks below and
 * hang their create forms into `workspace.create-types` build `LinksSection` into their detail panels and delete elements with `useDeleteElement`. The main route `trash` shows the deleted elements of all plugins. The state (search text, hidden and marked projects) is
 * kept in the UI state of the server.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	api: workspaceApi,
	slots: {
		"detail-sections": {
			description:
				"Widgets in the detail panel of every element (below its fields, drawn by `DetailSections`): the widget reads the element with `useDetailElement`.",
		},
		"element-detail": {
			description:
				"The detail view of an element kind, drawn by `ElementDetail`: `name` is the kind (e.g. `story`, `note`), the component reads the element with `useShownElement`.",
		},
		"attention-sources": {
			description:
				"Sources of due things (fired alarms, due notes …) for the bell in the projects section: a component without output that reports its entries with `useReportAttention`.",
		},
		"create-types": {
			description:
				"Forms of the dialog '＋ New': `name` is the kind, `component` the form (it uses `useCreateDialog`), the title is the text `create.<name>` of the contributing plugin.",
		},
	},
	eventHandlers: {
		"workspace.project.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Projects"]));
		},
		"workspace.element.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Trash", "Links"]));
		},
		"core.sync.state": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Sync", "Projects"]));
		},
		"workspace.links.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Links"]));
		},
		"core.reconnected": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Projects", "Links", "Trash", "Sync"]));
		},
	},
	contributions: [
		{ slot: "core.main", name: "trash", title: "tab.trash", icon: DeleteIcon, page: () => import("./pages/TrashPage"), layout: { sidebar: true, detail: true } },
		{ slot: "core.sidebar-sections", name: "search", component: SearchSection, order: 0 },
		{ slot: "core.sidebar-sections", name: "projects", component: ProjectsSection, order: 10 },
		{ slot: "layout-header-sidebar.header-actions", name: "new", component: NewButton, order: -10 },
		{ slot: "core.settings-sections", name: "projects", component: ProjectSettings, order: 0 },
	],
});

export { type AttentionAction, type AttentionEntry } from "./attention";
export { useReportAttention } from "./attentionContext";
export { useCreateDialog, type CreateDialogContext } from "./createDialog";
export { useProjectSelection, useSearchText } from "./state";
export { useListProjectsQuery, useSearchElementsQuery, type ElementOut, type Project } from "./api";
export { useDetailElement, type DetailElement } from "./detailElement";
export { DetailSections } from "./detailSections";
export { ElementDetail } from "./ElementDetail";
export { useShownElement, type ShownElement } from "./shownElement";
export { LinksSection } from "./LinksSection";
export { useDeleteElement } from "./useDeleteElement";
export { workspaceTestIds } from "./testIds";
