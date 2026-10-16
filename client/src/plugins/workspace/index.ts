import { definePlugin } from "../../core";
import { workspaceApi } from "./api";
import de from "./locales/de.json";
import en from "./locales/en.json";
import { NewButton } from "./NewButton";
import { ProjectsSection } from "./ProjectsSection";
import { SearchSection } from "./SearchSection";

/**
 * Projects, search and the "＋ New" dialog. Sections for the search and the projects hang in the sidebar of
 * the layout plugin, the button in its app bar. Other plugins read the public state through the hooks below and
 * hang their create forms into `workspace.create-types`. The state (search text, hidden and marked projects) is
 * kept in the UI state of the server.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	api: workspaceApi,
	slots: {
		"create-types": {
			description:
				"Forms of the dialog '＋ New': `name` is the kind, `component` the form (it uses `useCreateDialog`), the title is the text `create.<name>` of the contributing plugin.",
		},
	},
	eventHandlers: {
		"workspace.project.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Projects"]));
		},
		"core.reconnected": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Projects"]));
		},
	},
	contributions: [
		{ slot: "layout-header-sidebar.sidebar-sections", name: "search", component: SearchSection, order: 0 },
		{ slot: "layout-header-sidebar.sidebar-sections", name: "projects", component: ProjectsSection, order: 10 },
		{ slot: "layout-header-sidebar.header-actions", name: "new", component: NewButton, order: -10 },
	],
});

export { useCreateDialog, type CreateDialogContext } from "./createDialog";
export { useProjectSelection, useSearchText } from "./state";
export { useListProjectsQuery, type Project } from "./api";
export { workspaceTestIds } from "./testIds";
