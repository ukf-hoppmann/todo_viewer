import type { ContentOut, DocumentOut, DueOut, IndexedNote, IndexedTopic, NoteOut, SettingsOut } from "../../../client/src/plugins/notes/api";

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
		open_notes: 0,
		due_notes: 0,
		version: 1,
		...extra,
	};
}

/** A note of the index with plain defaults (project `p1`, waiting, no topic). */
export function note(uid: string, extra: Partial<IndexedNote> = {}): IndexedNote {
	return {
		uid,
		project_uid: "p1",
		label: uid.toUpperCase(),
		summary: `Note ${uid}`,
		status: "waiting",
		archived: false,
		topic_uid: null,
		review_at: "2026-11-15T12:00:00Z",
		version: 1,
		...extra,
	};
}

/** The detail of a note with plain defaults. */
export function noteDetail(uid: string, extra: Partial<NoteOut> = {}): NoteOut {
	return {
		uid,
		project_uid: "p1",
		label: uid.toUpperCase(),
		summary: `Note ${uid}`,
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
		...extra,
	};
}

export function notesDocument(name: string, content: string, extra: Partial<DocumentOut> = {}): DocumentOut {
	return { name, kind: name.includes("_notes") ? "notes" : "spec", content, version: 1, updated_at: "2026-10-16T12:00:00Z", ...extra };
}

export const emptyDue: DueOut = { count: 0, notes: [] };
export const defaultSettings: SettingsOut = { max_topic_depth: 3, review_days: 30 };
export const noContent: ContentOut = { topics: 0, active: 0, archived: 0 };
