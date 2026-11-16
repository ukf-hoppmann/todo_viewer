import { createPluginApi } from "../../core";
import type { components } from "../../shared";

export type NodeOut = components["schemas"]["NodeOut"];
export type TreeOut = components["schemas"]["TreeOut"];
export type DocumentOut = components["schemas"]["DocumentOut"];

/** The error of a write: the code and details the server gave, as an `Error` the forms can show. */
export class WriteError extends Error {
	constructor(
		message: string,
		readonly code: string | undefined,
		readonly details: Record<string, unknown>,
	) {
		super(message);
	}
}

/** Turns what a failed mutation throws (`unwrap()`) into a `WriteError`. */
export function toWriteError(failure: unknown): WriteError {
	if (failure instanceof WriteError) return failure;
	const data = (failure as { data?: { code?: string; message?: string; details?: Record<string, unknown> } } | undefined)?.data;
	return new WriteError(data?.message ?? "Request failed", data?.code, data?.details ?? {});
}

/** The message the server gave for a failed request, or the fallback. */
export function errorMessage(error: unknown, fallback: string): string {
	const data = (error as { data?: { message?: unknown } } | undefined)?.data;
	return typeof data?.message === "string" ? data.message : fallback;
}

/**
 * The API of the plugin (`mindmap.api`): `getTree` reads the topic tree of a project (the project is the root),
 * `createNode` and `updateNode` write a node, `moveNode` hangs a node with its branch under another parent (empty:
 * under the root) or to another place among its siblings. Moving to the trash goes through `workspace`. The tag `Tree` is what
 * server events invalidate. The documents of a node (`getDocument`, `putDocument`, `appendEntry`) have the tag
 * `Documents`; writing one also invalidates `Tree`, which lists the names of the documents of every node.
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
		moveNode: build.mutation<NodeOut, { uid: string; version: number; parent: string | null; position: number }>({
			query: ({ uid, ...body }) => ({ url: `mindmap/nodes/${uid}/move`, method: "POST", body }),
			invalidatesTags: ["Tree"],
		}),
		getDocument: build.query<DocumentOut, { uid: string; name: string }>({
			query: ({ uid, name }) => `mindmap/nodes/${uid}/documents/${name}`,
			providesTags: ["Documents"],
		}),
		putDocument: build.mutation<DocumentOut, { uid: string; name: string; content: string; version?: number }>({
			query: ({ uid, name, ...body }) => ({ url: `mindmap/nodes/${uid}/documents/${name}`, method: "PUT", body }),
			invalidatesTags: ["Tree", "Documents"],
		}),
		appendEntry: build.mutation<DocumentOut, { uid: string; topic: string; discussed: string[]; decided: string[]; open: string[] }>({
			query: ({ uid, ...body }) => ({ url: `mindmap/nodes/${uid}/entries`, method: "POST", body }),
			invalidatesTags: ["Tree", "Documents"],
		}),
	}),
	{ tagTypes: ["Tree", "Documents"] },
);

export const {
	useGetTreeQuery,
	useCreateNodeMutation,
	useUpdateNodeMutation,
	useMoveNodeMutation,
	useGetDocumentQuery,
	usePutDocumentMutation,
	useAppendEntryMutation,
} = mindmapApi;
