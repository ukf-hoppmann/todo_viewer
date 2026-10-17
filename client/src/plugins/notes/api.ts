import { createPluginApi } from "../../core";
import type { components } from "../../shared";

export type NotesIndex = components["schemas"]["NotesIndexOut"];
export type IndexedNote = components["schemas"]["NoteIndexOut"];
export type IndexedTopic = components["schemas"]["TopicOut"];
export type NoteOut = components["schemas"]["NoteOut"];
export type TopicRef = components["schemas"]["TopicRef"];
export type DueOut = components["schemas"]["DueOut"];
export type ContentOut = components["schemas"]["ContentOut"];
export type SettingsOut = components["schemas"]["SettingsOut"];
export type DocumentInfo = components["schemas"]["DocumentInfo"];
export type DocumentOut = components["schemas"]["DocumentOut"];
export type NoteNoticeOut = components["schemas"]["NoteNoticeOut"];
export type TriggerOut = components["schemas"]["TriggerOut"];
export type TargetRef = components["schemas"]["TargetRef"];
export type DueNoteOut = components["schemas"]["DueNoteOut"];
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

/** What the dialog of a topic with content sends: the choice for its notes. */
export interface TopicChoice {
	keep_archived: boolean;
	active_notes?: "delete" | "move" | "archive";
	move_to?: string | null;
}

/**
 * The API of the plugin (`notes.api`). `listIndex` asks for the topics and all notes of the given projects (the
 * status filter and the search are applied in the browser, so the counters and the folding stay independent of
 * them). The tag `Notes` is what server events invalidate, `Due` the counter in the app bar.
 */
export const notesApi = createPluginApi(
	"notes",
	(build) => ({
		listIndex: build.query<NotesIndex, string[]>({
			query: (projects) => ({ url: "notes/index", params: { projects: projects.join(",") } }),
			providesTags: ["Notes"],
		}),
		getNote: build.query<NoteOut, string>({
			query: (uid) => `notes/notes/${uid}`,
			providesTags: ["Notes"],
		}),
		getDue: build.query<DueOut, void>({
			query: () => "notes/due",
			providesTags: ["Notes", "Due"],
		}),
		createNote: build.mutation<NoteOut, { project: string; fields: Record<string, unknown> }>({
			query: (body) => ({ url: "notes/notes", method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		updateNote: build.mutation<NoteOut, { uid: string; version: number; fields: Record<string, unknown> }>({
			query: ({ uid, ...body }) => ({ url: `notes/notes/${uid}`, method: "PUT", body }),
			invalidatesTags: ["Notes"],
		}),
		noteAction: build.mutation<
			NoteOut,
			{ uid: string; version: number; action: "keep" | "snooze" | "finish" | "restore"; review_at?: string; status?: "done" | "dropped" }
		>({
			query: ({ uid, action, ...body }) => ({ url: `notes/notes/${uid}/${action}`, method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		addTrigger: build.mutation<NoteOut, { uid: string; kind: "event" | "topic_date"; target?: string; status?: string }>({
			query: ({ uid, ...body }) => ({ url: `notes/notes/${uid}/triggers`, method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		removeTrigger: build.mutation<NoteOut, string>({
			query: (uid) => ({ url: `notes/triggers/${uid}`, method: "DELETE" }),
			invalidatesTags: ["Notes"],
		}),
		decideNotice: build.mutation<DecisionOut, { uid: string; decision: string; version?: number; type?: string; fields?: Record<string, unknown> }>({
			query: ({ uid, ...body }) => ({ url: `notes/notices/${uid}/decide`, method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		listItemNotices: build.query<NoteNoticeOut[], string>({
			query: (uid) => `notes/items/${uid}/notices`,
			providesTags: ["Notes"],
		}),
		promoteNote: build.mutation<PromotedOut, { uid: string; version: number; type: string; fields: Record<string, unknown> }>({
			query: ({ uid, ...body }) => ({ url: `notes/notes/${uid}/promote`, method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		demoteItem: build.mutation<DemotedOut, { uid: string; version: number; topic?: string | null }>({
			query: ({ uid, ...body }) => ({ url: `notes/items/${uid}/demote`, method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		createTopic: build.mutation<{ uid: string }, { project: string; name: string; parent?: string | null; due_at?: string | null }>({
			query: (body) => ({ url: "notes/topics", method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		updateTopic: build.mutation<{ uid: string }, { uid: string; version: number; fields: Record<string, unknown> }>({
			query: ({ uid, ...body }) => ({ url: `notes/topics/${uid}`, method: "PUT", body }),
			invalidatesTags: ["Notes"],
		}),
		moveTopic: build.mutation<{ uid: string }, { uid: string; version: number; parent: string | null }>({
			query: ({ uid, ...body }) => ({ url: `notes/topics/${uid}/move`, method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		topicContent: build.query<ContentOut, string>({
			query: (uid) => `notes/topics/${uid}/content`,
			providesTags: ["Notes"],
		}),
		archiveTopic: build.mutation<{ uid: string }, { uid: string; version: number } & Partial<TopicChoice>>({
			query: ({ uid, ...body }) => ({ url: `notes/topics/${uid}/archive`, method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		reactivateTopic: build.mutation<{ uid: string }, { uid: string; version: number }>({
			query: ({ uid, ...body }) => ({ url: `notes/topics/${uid}/reactivate`, method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		deleteTopic: build.mutation<{ uid: string; count: number }, { uid: string; version: number } & Partial<TopicChoice>>({
			query: ({ uid, ...body }) => ({ url: `notes/topics/${uid}/delete`, method: "POST", body }),
			invalidatesTags: ["Notes"],
		}),
		getDocument: build.query<DocumentOut, { uid: string; name: string }>({
			query: ({ uid, name }) => `notes/notes/${uid}/documents/${name}`,
			providesTags: ["Documents"],
		}),
		putDocument: build.mutation<DocumentOut, { uid: string; name: string; content: string; version?: number }>({
			query: ({ uid, name, ...body }) => ({ url: `notes/notes/${uid}/documents/${name}`, method: "PUT", body }),
			invalidatesTags: ["Notes", "Documents"],
		}),
		appendEntry: build.mutation<DocumentOut, { uid: string; topic: string; discussed: string[]; decided: string[]; open: string[] }>({
			query: ({ uid, ...body }) => ({ url: `notes/notes/${uid}/entries`, method: "POST", body }),
			invalidatesTags: ["Notes", "Documents"],
		}),
		getSettings: build.query<SettingsOut, void>({
			query: () => "notes/settings",
			providesTags: ["Settings"],
		}),
		updateSettings: build.mutation<SettingsOut, Partial<SettingsOut>>({
			query: (body) => ({ url: "notes/settings", method: "PUT", body }),
			invalidatesTags: ["Settings", "Notes"],
		}),
	}),
	{ tagTypes: ["Notes", "Due", "Documents", "Settings"] },
);

export const {
	useListIndexQuery,
	useGetNoteQuery,
	useGetDueQuery,
	useCreateNoteMutation,
	useUpdateNoteMutation,
	useNoteActionMutation,
	useAddTriggerMutation,
	useRemoveTriggerMutation,
	useDecideNoticeMutation,
	useListItemNoticesQuery,
	usePromoteNoteMutation,
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
} = notesApi;
