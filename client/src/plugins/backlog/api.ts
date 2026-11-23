import { createPluginApi } from "../../core";
import type { components } from "../../shared";

export type IndexItem = components["schemas"]["IndexItem"];
export type ItemOut = components["schemas"]["ItemOut"];
export type ItemSummary = components["schemas"]["ItemSummary"];
export type RetypeOut = components["schemas"]["RetypeOut"];
export type DocumentOut = components["schemas"]["ItemDocumentOut"];
export type NotesStateOut = components["schemas"]["NotesStateOut"];
export type NotesEntryOut = components["schemas"]["NotesEntryOut"];
export type ReopenOut = components["schemas"]["ReopenOut"];

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
		createItem: build.mutation<ItemOut, { project: string; type: string; fields: Record<string, unknown> }>({
			query: (body) => ({ url: "backlog/items", method: "POST", body }),
			invalidatesTags: ["Items"],
		}),
		updateItem: build.mutation<ItemOut, { uid: string; version: number; fields: Record<string, unknown>; resolution?: string }>({
			query: ({ uid, ...body }) => ({ url: `backlog/items/${uid}`, method: "PUT", body }),
			invalidatesTags: ["Items"],
		}),
		moveItem: build.mutation<ItemOut, { uid: string; version: number; parent: string | null; position: number }>({
			query: ({ uid, ...body }) => ({ url: `backlog/items/${uid}/move`, method: "POST", body }),
			invalidatesTags: ["Items"],
		}),
		retypeItem: build.mutation<RetypeOut, { uid: string; version: number; type: string }>({
			query: ({ uid, ...body }) => ({ url: `backlog/items/${uid}/retype`, method: "POST", body }),
			invalidatesTags: ["Items"],
		}),
		reopenAncestors: build.mutation<ReopenOut, string>({
			query: (uid) => ({ url: `backlog/items/${uid}/reopen`, method: "POST", body: {} }),
			invalidatesTags: ["Items"],
		}),
		getDocument: build.query<DocumentOut, { uid: string; name: string }>({
			query: ({ uid, name }) => `backlog/items/${uid}/documents/${name}`,
			providesTags: ["Documents"],
		}),
		putDocument: build.mutation<DocumentOut, { uid: string; name: string; content: string; version?: number; summary?: string }>({
			query: ({ uid, name, ...body }) => ({ url: `backlog/items/${uid}/documents/${name}`, method: "PUT", body }),
			invalidatesTags: ["Items", "Documents"],
		}),
		deleteDocument: build.mutation<{ name: string; trash_uid: string }, { uid: string; name: string; version: number }>({
			query: ({ uid, name, version }) => ({ url: `backlog/items/${uid}/documents/${name}`, method: "DELETE", params: { version } }),
			invalidatesTags: ["Items", "Documents"],
		}),
		appendNote: build.mutation<
			DocumentOut,
			{ uid: string; topic: string; discussed: string[]; decided: string[]; open: string[]; summary?: string }
		>({
			query: ({ uid, ...body }) => ({ url: `backlog/items/${uid}/notes`, method: "POST", body }),
			invalidatesTags: ["Items", "Documents"],
		}),
		getNotesState: build.query<NotesStateOut, string>({
			query: (uid) => `backlog/items/${uid}/notes/state`,
			providesTags: ["Documents"],
		}),
		listNotesEntries: build.query<NotesEntryOut[], string>({
			query: (uid) => `backlog/items/${uid}/notes/entries`,
			providesTags: ["Documents"],
		}),
		getItem: build.query<ItemOut, string>({
			query: (uid) => `backlog/items/${uid}`,
			providesTags: ["Items"],
		}),
	}),
	{ tagTypes: ["Items", "Documents"] },
);

export const {
	useListItemsQuery,
	useGetItemQuery,
	useCreateItemMutation,
	useUpdateItemMutation,
	useMoveItemMutation,
	useRetypeItemMutation,
	useReopenAncestorsMutation,
	useGetDocumentQuery,
	usePutDocumentMutation,
	useDeleteDocumentMutation,
	useAppendNoteMutation,
	useGetNotesStateQuery,
	useListNotesEntriesQuery,
} = backlogApi;
