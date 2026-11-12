import type { ContentOut, DocumentOut, DueMemoOut, DueOut, IndexedMemo, IndexedTopic, MemoOut, SettingsOut } from "../../../client/src/plugins/memos/api";

/** A topic of the index with plain defaults (project `p1`, no parent, active). */
export function topic(uid: string, extra: Partial<IndexedTopic> = {}): IndexedTopic {
	return {
		uid,
		project_uid: "p1",
		label: uid.toUpperCase(),
		name: `Topic ${uid}`,
		parent_uid: null,
		due_at: null,
		archived: false,
		system: false,
		open_memos: 0,
		due_memos: 0,
		version: 1,
		...extra,
	};
}

/** A memo of the index with plain defaults (project `p1`, waiting, no topic). */
export function memo(uid: string, extra: Partial<IndexedMemo> = {}): IndexedMemo {
	return {
		uid,
		project_uid: "p1",
		label: uid.toUpperCase(),
		summary: `Memo ${uid}`,
		status: "waiting",
		archived: false,
		topic_uid: null,
		review_at: "2026-11-15T12:00:00Z",
		version: 1,
		...extra,
	};
}

/** The detail of a memo with plain defaults. */
export function memoDetail(uid: string, extra: Partial<MemoOut> = {}): MemoOut {
	return {
		uid,
		project_uid: "p1",
		label: uid.toUpperCase(),
		summary: `Memo ${uid}`,
		body: null,
		status: "waiting",
		stored_status: "waiting",
		archived: false,
		topic_uid: null,
		path: [],
		review_at: "2026-11-15T12:00:00Z",
		trigger_mode: "any",
		documents: [],
		version: 1,
		deleted: false,
		reason: null,
		triggers: [],
		hints: [],
		...extra,
	};
}

export function memosDocument(name: string, content: string, extra: Partial<DocumentOut> = {}): DocumentOut {
	return { name, kind: name.includes("_memos") ? "memos" : "spec", content, version: 1, updated_at: "2026-10-16T12:00:00Z", ...extra };
}

export const emptyDue: DueOut = { count: 0, memos: [] };
export const defaultSettings: SettingsOut = { max_topic_depth: 3, review_days: 30 };
export const noContent: ContentOut = { topics: 0, active: 0, archived: 0 };

/** A due memo of the counter list with plain defaults (project `p1`, reason review). */
export function dueMemo(uid: string, extra: Partial<DueMemoOut> = {}): DueMemoOut {
	return { uid, project_uid: "p1", label: uid.toUpperCase(), summary: `Memo ${uid}`, review_at: null, version: 1, reason: "review_expired", path: [], triggers: [], hints: [], due_since: null, ...extra };
}
