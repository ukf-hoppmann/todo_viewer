import { notesApi, type ContentOut, type DocumentOut, type DueOut, type IndexedNote, type IndexedTopic, type NoteOut, type SettingsOut } from "../../../client/src/plugins/notes/api";
import { fakeWorkspaceBackend } from "./fakeWorkspaceBackend";
import { defaultSettings, emptyDue, noContent } from "./notesFixtures";

type Options = Omit<Parameters<typeof fakeWorkspaceBackend>[0] & object, "respond" | "extraApis"> & {
	topics?: IndexedTopic[];
	notes?: IndexedNote[];
	/** The detail of a note by `uid`. */
	noteDetails?: Record<string, NoteOut>;
	/** The documents of a note by name. */
	noteDocuments?: Record<string, DocumentOut>;
	due?: DueOut;
	settings?: SettingsOut;
	/** The content of a topic by `uid` (for the dialog of delete and archive). */
	contents?: Record<string, ContentOut>;
	/** Answers a request itself; `undefined` lets the fake answer. */
	respond?: (request: { method: string; path: string; body?: unknown; query: URLSearchParams }) => Response | undefined;
};

/**
 * The workspace fake plus the `notes` API: it answers the index (by project), the detail, the counter, the contents
 * of topics, the settings and the documents, and echoes every write (the requests are in `calls`).
 */
export function fakeNotesBackend(options: Options = {}) {
	let settings = options.settings ?? defaultSettings;
	return fakeWorkspaceBackend({
		...options,
		extraApis: [{ id: "notes", api: notesApi }],
		respond: (request) => {
			const custom = options.respond?.(request);
			if (custom) return custom;
			const { method, path, query } = request;
			if (!path.startsWith("notes/")) return undefined;
			if (path === "notes/index") {
				const wanted = (query.get("projects") ?? "").split(",").filter(Boolean);
				return Response.json({
					topics: (options.topics ?? []).filter((entry) => wanted.includes(entry.project_uid)),
					notes: (options.notes ?? []).filter((entry) => wanted.includes(entry.project_uid)),
				});
			}
			if (path === "notes/due") return Response.json(options.due ?? emptyDue);
			if (path === "notes/settings") {
				if (method === "PUT") settings = { ...settings, ...(request.body as Partial<SettingsOut>) };
				return Response.json(settings);
			}
			const content = /^notes\/topics\/([^/]+)\/content$/.exec(path);
			if (content) return Response.json(options.contents?.[content[1]!] ?? noContent);
			const topicWrite = /^notes\/topics(?:\/([^/]+)(?:\/(\w+))?)?$/.exec(path);
			if (topicWrite && method !== "GET") return Response.json({ uid: topicWrite[1] ?? "new", count: 0 });
			const document = /^notes\/notes\/([^/]+)\/documents\/([^/]+)$/.exec(path);
			if (document) {
				const found = options.noteDocuments?.[document[2]!];
				if (method === "GET") return found ? Response.json(found) : Response.json({ code: "document_not_found", message: "Dokument gibt es nicht", details: {} }, { status: 400 });
				return Response.json({ ...(found ?? { name: document[2], kind: "spec", updated_at: "2026-10-17T12:00:00Z" }), ...(request.body as object), version: (found?.version ?? 0) + 1 });
			}
			const one = /^notes\/notes\/([^/]+)(?:\/(\w+))?$/.exec(path);
			if (one) {
				const detail = options.noteDetails?.[one[1]!];
				if (method === "GET") return detail ? Response.json(detail) : Response.json({ code: "not_found", message: "Note gibt es nicht", details: {} }, { status: 404 });
				return Response.json(detail ?? { ...(request.body as object), uid: one[1] ?? "new", version: 2 });
			}
			if (path === "notes/notes" && method === "POST") return Response.json({ uid: "new", version: 1 });
			return undefined;
		},
	});
}
