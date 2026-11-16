import { createPluginApi } from "../../core";
import type { components } from "../../shared";

export type NodeOut = components["schemas"]["NodeOut"];
export type TreeOut = components["schemas"]["TreeOut"];

/** The message the server gave for a failed request, or the fallback. */
export function errorMessage(error: unknown, fallback: string): string {
	const data = (error as { data?: { message?: unknown } } | undefined)?.data;
	return typeof data?.message === "string" ? data.message : fallback;
}

/**
 * The API of the plugin (`mindmap.api`): `getTree` reads the topic tree of a project (the project is the root),
 * `createNode` and `updateNode` write a node. Moving to the trash goes through `workspace`. The tag `Tree` is what
 * server events invalidate.
 */
export const mindmapApi = createPluginApi(
	"mindmap",
	(build) => ({
		getTree: build.query<TreeOut, string>({
			query: (project) => ({ url: `mindmap/trees/${project}` }),
			providesTags: ["Tree"],
		}),
		createNode: build.mutation<NodeOut, { project: string; title: string; parent?: string; position?: number }>({
			query: (body) => ({ url: "mindmap/nodes", method: "POST", body }),
			invalidatesTags: ["Tree"],
		}),
		updateNode: build.mutation<NodeOut, { uid: string; version: number; title?: string; text?: string }>({
			query: ({ uid, ...body }) => ({ url: `mindmap/nodes/${uid}`, method: "PUT", body }),
			invalidatesTags: ["Tree"],
		}),
	}),
	{ tagTypes: ["Tree"] },
);

export const { useGetTreeQuery, useCreateNodeMutation, useUpdateNodeMutation } = mindmapApi;
