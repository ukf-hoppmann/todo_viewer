import { memosApi, type MemoHintOut, type ContentOut, type DocumentOut, type DueOut, type IndexedMemo, type IndexedTopic, type MemoOut, type SettingsOut } from "../../../client/src/plugins/memos/api";
import { fakeWorkspaceBackend } from "./fakeWorkspaceBackend";
import { defaultSettings, emptyDue, noContent, memoDetail } from "./memosFixtures";

type Options = Omit<Parameters<typeof fakeWorkspaceBackend>[0] & object, "respond" | "extraApis"> & {
	topics?: IndexedTopic[];
	memos?: IndexedMemo[];
	/** The detail of a memo by `uid`. */
	memoDetails?: Record<string, MemoOut>;
	/** The documents of a memo by name. */
	memoDocuments?: Record<string, DocumentOut>;
	due?: DueOut;
	settings?: SettingsOut;
	/** The open hints of an item by `uid` (`GET memos/items/{uid}/hints`). */
	itemHints?: Record<string, MemoHintOut[]>;
	/** The content of a topic by `uid` (for the dialog of delete and archive). */
	contents?: Record<string, ContentOut>;
	/** Answers a request itself; `undefined` lets the fake answer. */
	respond?: (request: { method: string; path: string; body?: unknown; query: URLSearchParams }) => Response | undefined;
};

/**
 * The workspace fake plus the `memos` API: it answers the index (by project), the detail, the counter, the contents
 * of topics, the settings and the documents, and echoes every write (the requests are in `calls`).
 */
export function fakeMemosBackend(options: Options = {}) {
	let settings = options.settings ?? defaultSettings;
	return fakeWorkspaceBackend({
		...options,
		extraApis: [{ id: "memos", api: memosApi }],
		respond: (request) => {
			const custom = options.respond?.(request);
			if (custom) return custom;
			const { method, path, query } = request;
			if (!path.startsWith("memos/")) return undefined;
			if (path === "memos/index") {
				const wanted = (query.get("projects") ?? "").split(",").filter(Boolean);
				return Response.json({
					topics: (options.topics ?? []).filter((entry) => wanted.includes(entry.project_uid)),
					memos: (options.memos ?? []).filter((entry) => wanted.includes(entry.project_uid)),
				});
			}
			if (path === "memos/due") return Response.json(options.due ?? emptyDue);
			if (path === "memos/settings") {
				if (method === "PUT") settings = { ...settings, ...(request.body as Partial<SettingsOut>) };
				return Response.json(settings);
			}
			const itemHints = /^memos\/items\/([^/]+)\/hints$/.exec(path);
			if (itemHints) return Response.json(options.itemHints?.[itemHints[1]!] ?? []);
			const demote = /^memos\/items\/([^/]+)\/demote$/.exec(path);
			if (demote) return Response.json({ memo: memoDetail("new", { label: "MEMO-009" }), item_uid: demote[1] });
			const promote = /^memos\/memos\/([^/]+)\/promote$/.exec(path);
			if (promote) return Response.json({ memo: options.memoDetails?.[promote[1]!] ?? memoDetail(promote[1]!), item_uid: "item-new" });
			const decide = /^memos\/hints\/([^/]+)\/decide$/.exec(path);
			if (decide) return Response.json({ hint: { uid: decide[1], kind: "item_completed", created_at: "2026-10-17T00:00:00Z", source: null, decisions: [] }, memo: null });
			const removeTrigger = /^memos\/triggers\/([^/]+)$/.exec(path);
			if (removeTrigger) return Response.json(Object.values(options.memoDetails ?? {})[0] ?? memoDetail("n1"));
			const content = /^memos\/topics\/([^/]+)\/content$/.exec(path);
			if (content) return Response.json(options.contents?.[content[1]!] ?? noContent);
			const topicWrite = /^memos\/topics(?:\/([^/]+)(?:\/(\w+))?)?$/.exec(path);
			if (topicWrite && method !== "GET") return Response.json({ uid: topicWrite[1] ?? "new", count: 0 });
			const document = /^memos\/memos\/([^/]+)\/documents\/([^/]+)$/.exec(path);
			if (document) {
				const found = options.memoDocuments?.[document[2]!];
				if (method === "GET") return found ? Response.json(found) : Response.json({ code: "document_not_found", message: "Dokument gibt es nicht", details: {} }, { status: 400 });
				return Response.json({ ...(found ?? { name: document[2], kind: "spec", updated_at: "2026-10-17T12:00:00Z" }), ...(request.body as object), version: (found?.version ?? 0) + 1 });
			}
			const one = /^memos\/memos\/([^/]+)(?:\/(\w+))?$/.exec(path);
			if (one) {
				const detail = options.memoDetails?.[one[1]!];
				if (method === "GET") return detail ? Response.json(detail) : Response.json({ code: "not_found", message: "Memo gibt es nicht", details: {} }, { status: 404 });
				return Response.json(detail ?? { ...(request.body as object), uid: one[1] ?? "new", version: 2 });
			}
			if (path === "memos/memos" && method === "POST") return Response.json({ uid: "new", version: 1 });
			return undefined;
		},
	});
}
