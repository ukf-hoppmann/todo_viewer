import { createPluginApi } from "../../core";
import type { components } from "../../shared";

export type MemosIndex = components["schemas"]["MemosIndexOut"];
export type IndexedMemo = components["schemas"]["MemoIndexOut"];
export type IndexedTopic = components["schemas"]["TopicOut"];
export type MemoOut = components["schemas"]["MemoOut"];
export type TopicRef = components["schemas"]["TopicRef"];
export type DueOut = components["schemas"]["DueOut"];
export type ContentOut = components["schemas"]["ContentOut"];
export type SettingsOut = components["schemas"]["SettingsOut"];
export type DocumentInfo = components["schemas"]["DocumentInfo"];
export type DocumentOut = components["schemas"]["DocumentOut"];
export type MemoHintOut = components["schemas"]["MemoHintOut"];
export type TriggerOut = components["schemas"]["TriggerOut"];
export type TargetRef = components["schemas"]["TargetRef"];
export type DueMemoOut = components["schemas"]["DueMemoOut"];
export type DecisionOut = components["schemas"]["DecisionOut"];
export type PromotedOut = components["schemas"]["PromotedOut"];
export type DemotedOut = components["schemas"]["DemotedOut"];

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

/** What the dialog of a topic with content sends: the choice for its memos. */
export interface TopicChoice {
	keep_archived: boolean;
	active_memos?: "delete" | "move" | "archive";
	move_to?: string | null;
}

/**
 * The API of the plugin (`memos.api`). `listIndex` asks for the topics and all memos of the given projects (the
 * status filter and the search are applied in the browser, so the counters and the folding stay independent of
 * them). The tag `Memos` is what server events invalidate, `Due` the counter in the app bar.
 */
export const memosApi = createPluginApi(
	"memos",
	(build) => ({
		listIndex: build.query<MemosIndex, string[]>({
			query: (projects) => ({ url: "memos/index", params: { projects: projects.join(",") } }),
			providesTags: ["Memos"],
		}),
		getMemo: build.query<MemoOut, string>({
			query: (uid) => `memos/memos/${uid}`,
			providesTags: ["Memos"],
		}),
		getDue: build.query<DueOut, void>({
			query: () => "memos/due",
			providesTags: ["Memos", "Due"],
		}),
		createMemo: build.mutation<MemoOut, { project: string; fields: Record<string, unknown> }>({
			query: (body) => ({ url: "memos/memos", method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		updateMemo: build.mutation<MemoOut, { uid: string; version: number; fields: Record<string, unknown> }>({
			query: ({ uid, ...body }) => ({ url: `memos/memos/${uid}`, method: "PUT", body }),
			invalidatesTags: ["Memos"],
		}),
		memoAction: build.mutation<
			MemoOut,
			{ uid: string; version: number; action: "keep" | "snooze" | "finish" | "restore"; review_at?: string; status?: "done" | "dropped" }
		>({
			query: ({ uid, action, ...body }) => ({ url: `memos/memos/${uid}/${action}`, method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		addTrigger: build.mutation<MemoOut, { uid: string; kind: "event" | "topic_date"; target?: string; status?: string }>({
			query: ({ uid, ...body }) => ({ url: `memos/memos/${uid}/triggers`, method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		removeTrigger: build.mutation<MemoOut, string>({
			query: (uid) => ({ url: `memos/triggers/${uid}`, method: "DELETE" }),
			invalidatesTags: ["Memos"],
		}),
		decideHint: build.mutation<DecisionOut, { uid: string; decision: string; version?: number; type?: string; fields?: Record<string, unknown> }>({
			query: ({ uid, ...body }) => ({ url: `memos/hints/${uid}/decide`, method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		listItemHints: build.query<MemoHintOut[], string>({
			query: (uid) => `memos/items/${uid}/hints`,
			providesTags: ["Memos"],
		}),
		promoteMemo: build.mutation<PromotedOut, { uid: string; version: number; type: string; fields: Record<string, unknown> }>({
			query: ({ uid, ...body }) => ({ url: `memos/memos/${uid}/promote`, method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		demoteItem: build.mutation<DemotedOut, { uid: string; version: number; topic?: string | null }>({
			query: ({ uid, ...body }) => ({ url: `memos/items/${uid}/demote`, method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		createTopic: build.mutation<{ uid: string }, { project: string; name: string; parent?: string | null; due_at?: string | null }>({
			query: (body) => ({ url: "memos/topics", method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		updateTopic: build.mutation<{ uid: string }, { uid: string; version: number; fields: Record<string, unknown> }>({
			query: ({ uid, ...body }) => ({ url: `memos/topics/${uid}`, method: "PUT", body }),
			invalidatesTags: ["Memos"],
		}),
		moveTopic: build.mutation<{ uid: string }, { uid: string; version: number; parent: string | null }>({
			query: ({ uid, ...body }) => ({ url: `memos/topics/${uid}/move`, method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		topicContent: build.query<ContentOut, string>({
			query: (uid) => `memos/topics/${uid}/content`,
			providesTags: ["Memos"],
		}),
		archiveTopic: build.mutation<{ uid: string }, { uid: string; version: number } & Partial<TopicChoice>>({
			query: ({ uid, ...body }) => ({ url: `memos/topics/${uid}/archive`, method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		reactivateTopic: build.mutation<{ uid: string }, { uid: string; version: number }>({
			query: ({ uid, ...body }) => ({ url: `memos/topics/${uid}/reactivate`, method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		deleteTopic: build.mutation<{ uid: string; count: number }, { uid: string; version: number } & Partial<TopicChoice>>({
			query: ({ uid, ...body }) => ({ url: `memos/topics/${uid}/delete`, method: "POST", body }),
			invalidatesTags: ["Memos"],
		}),
		getDocument: build.query<DocumentOut, { uid: string; name: string }>({
			query: ({ uid, name }) => `memos/memos/${uid}/documents/${name}`,
			providesTags: ["Documents"],
		}),
		putDocument: build.mutation<DocumentOut, { uid: string; name: string; content: string; version?: number }>({
			query: ({ uid, name, ...body }) => ({ url: `memos/memos/${uid}/documents/${name}`, method: "PUT", body }),
			invalidatesTags: ["Memos", "Documents"],
		}),
		appendEntry: build.mutation<DocumentOut, { uid: string; topic: string; discussed: string[]; decided: string[]; open: string[] }>({
			query: ({ uid, ...body }) => ({ url: `memos/memos/${uid}/entries`, method: "POST", body }),
			invalidatesTags: ["Memos", "Documents"],
		}),
		getSettings: build.query<SettingsOut, void>({
			query: () => "memos/settings",
			providesTags: ["Settings"],
		}),
		updateSettings: build.mutation<SettingsOut, Partial<SettingsOut>>({
			query: (body) => ({ url: "memos/settings", method: "PUT", body }),
			invalidatesTags: ["Settings", "Memos"],
		}),
	}),
	{ tagTypes: ["Memos", "Due", "Documents", "Settings"] },
);

export const {
	useListIndexQuery,
	useGetMemoQuery,
	useGetDueQuery,
	useCreateMemoMutation,
	useUpdateMemoMutation,
	useMemoActionMutation,
	useAddTriggerMutation,
	useRemoveTriggerMutation,
	useDecideHintMutation,
	useListItemHintsQuery,
	usePromoteMemoMutation,
	useDemoteItemMutation,
	useCreateTopicMutation,
	useUpdateTopicMutation,
	useMoveTopicMutation,
	useTopicContentQuery,
	useArchiveTopicMutation,
	useReactivateTopicMutation,
	useDeleteTopicMutation,
	useGetDocumentQuery,
	usePutDocumentMutation,
	useAppendEntryMutation,
	useGetSettingsQuery,
	useUpdateSettingsMutation,
} = memosApi;
