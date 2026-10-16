import { createPluginApi } from "../../core";
import type { components } from "../../shared";

export type IndexItem = components["schemas"]["IndexItem"];
export type ItemOut = components["schemas"]["ItemOut"];
export type ItemSummary = components["schemas"]["ItemSummary"];

/**
 * The API of the plugin (`backlog.api`). `listItems` asks for the items of the given projects (all statuses;
 * the filters of the sidebar are applied in the browser so that the progress and the folding stay independent of
 * them), `getItem` for one item with all its fields. The tag `Items` is what server events invalidate.
 */
export const backlogApi = createPluginApi(
	"backlog",
	(build) => ({
		listItems: build.query<IndexItem[], string[]>({
			query: (projects) => ({ url: "backlog/items", params: { projects: projects.join(",") } }),
			providesTags: ["Items"],
		}),
		getItem: build.query<ItemOut, string>({
			query: (uid) => `backlog/items/${uid}`,
			providesTags: ["Items"],
		}),
	}),
	{ tagTypes: ["Items"] },
);

export const { useListItemsQuery, useGetItemQuery } = backlogApi;
