import { createPluginApi } from "../../core";
import type { components } from "../../shared";

export type NodeOut = components["schemas"]["NodeOut"];
export type TreeOut = components["schemas"]["TreeOut"];
export type TreeNodeOut = components["schemas"]["TreeNodeOut"];
export type ItemRefOut = components["schemas"]["ItemRefOut"];
export type NodeItemOut = components["schemas"]["NodeItemOut"];
export type MemoRefOut = components["schemas"]["MemoRefOut"];
export type NodeContentOut = components["schemas"]["NodeContentOut"];
export type ItemNodeOut = components["schemas"]["ItemNodeOut"];
export type DocumentOut = components["schemas"]["DocumentOut"];
export type MapOut = components["schemas"]["MapOut"];
export type MapDeletedOut = components["schemas"]["MapDeletedOut"];
export type RemovalOut = components["schemas"]["RemovalOut"];
export type NodeTreeOut = components["schemas"]["NodeTreeOut"];
export type RemovedFromOut = components["schemas"]["RemovedFromOut"];
export type TrashedNodeOut = components["schemas"]["TrashedNodeOut"];
export type PlacementRestoredOut = components["schemas"]["PlacementRestoredOut"];

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
 * The API of the plugin (`mindmap.api`): `getTree` reads the topic tree of a project (the project is the root) with
 * count, progress and state of every node and the items without a node; `getTrees` reads the trees of several projects at once (the overall view; one tree per project, in the order given); `statuses` is the status filter of the
 * backlog (comma-separated, empty: all),
 * `listMaps` lists the maps of a project (the project tree first, then the free maps, each with its node count), `createMap`, `renameMap` and `deleteMap` (into the trash) write them (tag `Maps`); `getTree`, `createNode` and `getNodeContent` take the free map as `tree`.
 * `moveNodeToMap` hangs a branch into another map, `transferNodeToMap` puts it into another map too (same records, structure below per tree), `removeNodeFromMap` takes it out of one map ("Hier entfernen"), `deleteNode` out of all ("Knoten löschen"); `listNodeTrees` lists the maps a node stands in.
 * `listTrashedNodes` lists the deleted branches of a map (the side view "Papierkorb", tag `Trashed`), `restoreAndMoveNode` brings one back to a new place of the map ("wiederherstellen und umziehen").
 * `createNode` and `updateNode` write a node, `moveNode` hangs a node with its branch under another parent (empty:
 * under the root) or to another place among its siblings. Moving to the trash goes through `workspace`. The tag `Tree` is what
 * server events invalidate. The documents of a node (`getDocument`, `putDocument`, `appendEntry`) have the tag
 * `Documents`; writing one also invalidates `Tree`, which lists the names of the documents of every node.
 */
export const mindmapApi = createPluginApi(
	"mindmap",
	(build) => ({
		getTree: build.query<TreeOut, { project: string; statuses: string; tree?: string }>({
			// Without `tree` the project tree, else a free map of the project.
			query: ({ project, statuses, tree }) => ({ url: `mindmap/trees/${project}`, params: { ...(statuses ? { statuses } : {}), ...(tree ? { tree } : {}) } }),
			providesTags: ["Tree"],
		}),
		listMaps: build.query<MapOut[], string>({
			query: (project) => `mindmap/maps/${project}`,
			providesTags: ["Maps"],
		}),
		createMap: build.mutation<MapOut, { project: string; name: string }>({
			query: (body) => ({ url: "mindmap/maps", method: "POST", body }),
			invalidatesTags: ["Maps"],
		}),
		renameMap: build.mutation<MapOut, { tree: string; version: number; name: string }>({
			query: ({ tree, ...body }) => ({ url: `mindmap/maps/${tree}`, method: "PUT", body }),
			invalidatesTags: ["Maps"],
		}),
		deleteMap: build.mutation<MapDeletedOut, { tree: string; version: number }>({
			query: ({ tree, version }) => ({ url: `mindmap/maps/${tree}`, method: "DELETE", params: { version } }),
			invalidatesTags: ["Maps", "Tree", "Content"],
		}),
		getTrees: build.query<TreeOut[], { projects: string[]; statuses: string }>({
			// One request per project, in parallel, so the overall view needs no hook in a loop.
			async queryFn({ projects, statuses }, _api, _extra, baseQuery) {
				const results = await Promise.all(
					projects.map((project) => baseQuery({ url: `mindmap/trees/${project}`, params: statuses ? { statuses } : undefined })),
				);
				const failed = results.find((result) => result.error);
				if (failed?.error) return { error: failed.error };
				return { data: results.map((result) => result.data as TreeOut) };
			},
			providesTags: ["Tree"],
		}),
		getNodeContent: build.query<NodeContentOut, { node: string; statuses: string; tree?: string }>({
			query: ({ node, statuses, tree }) => ({ url: `mindmap/nodes/${node}/content`, params: { ...(statuses ? { statuses } : {}), ...(tree ? { tree } : {}) } }),
			providesTags: ["Content"],
		}),
		getItemNode: build.query<ItemNodeOut, string>({
			query: (item) => `mindmap/items/${item}/node`,
			providesTags: ["ItemNode"],
		}),
		assignItem: build.mutation<NodeOut, { node: string; item: string; replace?: boolean }>({
			query: ({ node, ...body }) => ({ url: `mindmap/nodes/${node}/items`, method: "POST", body }),
			invalidatesTags: ["Tree", "Content", "ItemNode"],
		}),
		unassignItem: build.mutation<unknown, string>({
			query: (item) => ({ url: `mindmap/items/${item}/node`, method: "DELETE" }),
			invalidatesTags: ["Tree", "Content", "ItemNode"],
		}),
		linkMemo: build.mutation<NodeOut, { node: string; memo: string }>({
			query: ({ node, ...body }) => ({ url: `mindmap/nodes/${node}/memos`, method: "POST", body }),
			invalidatesTags: ["Content"],
		}),
		unlinkMemo: build.mutation<unknown, { node: string; memo: string }>({
			query: ({ node, memo }) => ({ url: `mindmap/nodes/${node}/memos/${memo}`, method: "DELETE" }),
			invalidatesTags: ["Content"],
		}),
		createNode: build.mutation<NodeOut, { project: string; title: string; parent?: string; position?: number; tree?: string }>({
			query: (body) => ({ url: "mindmap/nodes", method: "POST", body }),
			invalidatesTags: ["Tree", "Maps"],
		}),
		updateNode: build.mutation<NodeOut, { uid: string; version: number; title?: string; text?: string }>({
			query: ({ uid, ...body }) => ({ url: `mindmap/nodes/${uid}`, method: "PUT", body }),
			invalidatesTags: ["Tree"],
		}),
		moveNode: build.mutation<NodeOut, { uid: string; version: number; parent: string | null; position: number }>({
			query: ({ uid, ...body }) => ({ url: `mindmap/nodes/${uid}/move`, method: "POST", body }),
			invalidatesTags: ["Tree"],
		}),
		// Branches between trees (`TASK-063`): `ref` is the node, `target` the map (the `tree_uid` of `listMaps`, for a project
		// tree without a node its project uid), `tree` the tree the branch comes from (needed when it stands in several).
		moveNodeToMap: build.mutation<NodeOut, { ref: string; version: number; target: string; tree?: string }>({
			query: ({ ref, ...body }) => ({ url: `mindmap/nodes/${ref}/move-to-map`, method: "POST", body }),
			invalidatesTags: ["Tree", "Maps", "Content"],
		}),
		transferNodeToMap: build.mutation<NodeOut, { ref: string; version: number; target: string; tree?: string }>({
			query: ({ ref, ...body }) => ({ url: `mindmap/nodes/${ref}/transfer`, method: "POST", body }),
			invalidatesTags: ["Tree", "Maps", "Content"],
		}),
		removeNodeFromMap: build.mutation<RemovalOut, { ref: string; version: number; tree?: string }>({
			query: ({ ref, ...body }) => ({ url: `mindmap/nodes/${ref}/remove`, method: "POST", body }),
			invalidatesTags: ["Tree", "Maps", "Content"],
		}),
		deleteNode: build.mutation<RemovalOut, { ref: string; version: number }>({
			query: ({ ref, version }) => ({ url: `mindmap/nodes/${ref}`, method: "DELETE", params: { version } }),
			invalidatesTags: ["Tree", "Maps", "Content"],
		}),
		listNodeTrees: build.query<NodeTreeOut[], string>({
			query: (ref) => `mindmap/nodes/${ref}/trees`,
			providesTags: ["Tree", "Maps"],
		}),
		// Removed placements (`TASK-066`): `listRemovedPlacements` names the trees a node was taken out of ("Früher in …"),
		// `restoreNodePlacement` puts the branch back where it stood (under the root of the map when its old parent is gone).
		listRemovedPlacements: build.query<RemovedFromOut[], string>({
			query: (ref) => `mindmap/nodes/${ref}/removed`,
			providesTags: ["Tree", "Maps"],
		}),
		restoreNodePlacement: build.mutation<PlacementRestoredOut, { ref: string; version: number; tree?: string }>({
			query: ({ ref, ...body }) => ({ url: `mindmap/nodes/${ref}/restore-placement`, method: "POST", body }),
			invalidatesTags: ["Tree", "Maps", "Content"],
		}),
		// The trash of a map (`TASK-067`): the deleted branches that stood in `tree` (none: the project tree); `restoreAndMoveNode`
		// takes one out of the trash and puts it under `parent` (none: below the root) at `position` of `tree`.
		listTrashedNodes: build.query<TrashedNodeOut[], { project: string; tree?: string }>({
			query: ({ project, tree }) => ({ url: `mindmap/trash/${project}`, params: tree ? { tree } : undefined }),
			providesTags: ["Trashed"],
		}),
		restoreAndMoveNode: build.mutation<NodeOut, { ref: string; version: number; tree?: string; parent?: string | null; position?: number }>({
			query: ({ ref, parent, ...body }) => ({ url: `mindmap/nodes/${ref}/restore-move`, method: "POST", body: { ...body, ...(parent ? { parent } : {}) } }),
			invalidatesTags: ["Tree", "Maps", "Content", "Trashed"],
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
	{ tagTypes: ["Tree", "Documents", "Content", "ItemNode", "Maps", "Trashed"] },
);

export const {
	useGetTreeQuery,
	useGetTreesQuery,
	useListMapsQuery,
	useCreateMapMutation,
	useRenameMapMutation,
	useDeleteMapMutation,
	useGetNodeContentQuery,
	useGetItemNodeQuery,
	useAssignItemMutation,
	useUnassignItemMutation,
	useLinkMemoMutation,
	useUnlinkMemoMutation,
	useCreateNodeMutation,
	useUpdateNodeMutation,
	useMoveNodeMutation,
	useMoveNodeToMapMutation,
	useTransferNodeToMapMutation,
	useRemoveNodeFromMapMutation,
	useDeleteNodeMutation,
	useListNodeTreesQuery,
	useListRemovedPlacementsQuery,
	useRestoreNodePlacementMutation,
	useListTrashedNodesQuery,
	useRestoreAndMoveNodeMutation,
	useGetDocumentQuery,
	usePutDocumentMutation,
	useAppendEntryMutation,
} = mindmapApi;
