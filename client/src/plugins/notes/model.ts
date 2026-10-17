import type { FlatNode } from "../../shared";
import type { IndexedNote, IndexedTopic } from "./api";
import { statusColor } from "./constants";

export interface Filters {
	shownStatuses: ReadonlySet<string>;
	search: string;
	showArchivedTopics: boolean;
}

/** The uids of the topics that are hidden: archived ones (unless shown) with everything below them. */
export function hiddenTopics(topics: readonly IndexedTopic[], showArchivedTopics: boolean): Set<string> {
	const hidden = new Set<string>();
	if (showArchivedTopics) return hidden;
	const byUid = new Map(topics.map((topic) => [topic.uid, topic]));
	const isHidden = (topic: IndexedTopic, seen: Set<string>): boolean => {
		if (topic.archived) return true;
		const parent = topic.parent_uid ? byUid.get(topic.parent_uid) : undefined;
		if (!parent || seen.has(parent.uid)) return false;
		return isHidden(parent, new Set([...seen, topic.uid]));
	};
	for (const topic of topics) if (isHidden(topic, new Set())) hidden.add(topic.uid);
	return hidden;
}

function matches(note: IndexedNote, query: string): boolean {
	return !query || note.summary.toLowerCase().includes(query) || note.label.toLowerCase().includes(query);
}

/** The notes the filters let through: status shown, text found, and not inside a hidden topic. */
export function filterNotes(notes: readonly IndexedNote[], topics: readonly IndexedTopic[], filters: Filters): IndexedNote[] {
	const query = filters.search.trim().toLowerCase();
	const hidden = hiddenTopics(topics, filters.showArchivedTopics);
	return notes.filter((note) => filters.shownStatuses.has(note.status) && matches(note, query) && !(note.topic_uid && hidden.has(note.topic_uid)));
}

/** The topics to show: not hidden; with a search only those whose name matches or that lead to a found note. */
export function filterTopics(topics: readonly IndexedTopic[], shownNotes: readonly IndexedNote[], filters: Filters): IndexedTopic[] {
	const hidden = hiddenTopics(topics, filters.showArchivedTopics);
	const visible = topics.filter((topic) => !hidden.has(topic.uid));
	const query = filters.search.trim().toLowerCase();
	if (!query) return visible;
	const byUid = new Map(visible.map((topic) => [topic.uid, topic]));
	const keep = new Set<string>();
	const keepWithPath = (uid: string | null) => {
		for (let current = uid ? byUid.get(uid) : undefined; current && !keep.has(current.uid); current = current.parent_uid ? byUid.get(current.parent_uid) : undefined) {
			keep.add(current.uid);
		}
	};
	for (const topic of visible) if (topic.name.toLowerCase().includes(query) || topic.label.toLowerCase().includes(query)) keepWithPath(topic.uid);
	for (const note of shownNotes) keepWithPath(note.topic_uid);
	return visible.filter((topic) => keep.has(topic.uid));
}

/** How deep a topic stands (a root topic has depth 1). */
function depthOf(topic: IndexedTopic, byUid: ReadonlyMap<string, IndexedTopic>): number {
	let depth = 1;
	for (let current = topic; current.parent_uid && byUid.has(current.parent_uid) && depth < 50; depth++) current = byUid.get(current.parent_uid)!;
	return depth;
}

/**
 * The nodes of the shared tree for one project: topics (with the number of shown notes below them and, if the
 * extended marking is on, the area of the topics of the first two levels) and notes. Siblings: those with due
 * notes first, topics before notes, then by label.
 */
export function toFlatNodes(topics: readonly IndexedTopic[], notes: readonly IndexedNote[], extendedMarking: boolean): FlatNode[] {
	const byUid = new Map(topics.map((topic) => [topic.uid, topic]));
	const counts = new Map<string, number>();
	for (const note of notes) {
		for (let current = note.topic_uid ? byUid.get(note.topic_uid) : undefined, guard = 0; current && guard < 50; guard++) {
			counts.set(current.uid, (counts.get(current.uid) ?? 0) + 1);
			current = current.parent_uid ? byUid.get(current.parent_uid) : undefined;
		}
	}
	// Topics of the first level start an area, those of the second a nested one; deeper ones belong to the latter.
	const areaOf = (topic: IndexedTopic): 1 | 2 | undefined => (extendedMarking ? (depthOf(topic, byUid) <= 1 ? 1 : 2) : undefined);
	const dueFirst = (hasDue: boolean) => (hasDue ? 0 : 1);
	const topicNodes = topics.map((topic) => ({
		order: [dueFirst(topic.due_notes > 0), 0, topic.label] as const,
		node: {
			id: topic.uid,
			parentId: topic.parent_uid && byUid.has(topic.parent_uid) ? topic.parent_uid : null,
			label: topic.name,
			badge: topic.label,
			tag: "Topic",
			count: counts.get(topic.uid) ?? 0,
			area: areaOf(topic),
			dashed: topic.archived,
		} satisfies FlatNode,
	}));
	const noteNodes = notes.map((note) => {
		const topic = note.topic_uid ? byUid.get(note.topic_uid) : undefined;
		return {
			order: [dueFirst(note.status === "due"), 1, note.label] as const,
			node: {
				id: note.uid,
				parentId: topic ? topic.uid : null,
				label: note.summary,
				badge: note.label,
				tag: "Note",
				tagColor: statusColor(note.status),
				statusColor: statusColor(note.status),
				area: topic ? areaOf(topic) : undefined,
				dashed: note.archived,
			} satisfies FlatNode,
		};
	});
	return [...topicNodes, ...noteNodes]
		.sort((a, b) => a.order[0] - b.order[0] || a.order[1] - b.order[1] || a.order[2].localeCompare(b.order[2], undefined, { numeric: true }))
		.map((entry) => entry.node);
}

/** The uids of all topics (they can be folded). */
export function collapsibleIds(topics: readonly IndexedTopic[], notes: readonly IndexedNote[]): string[] {
	const parents = new Set([...topics.flatMap((t) => (t.parent_uid ? [t.parent_uid] : [])), ...notes.flatMap((n) => (n.topic_uid ? [n.topic_uid] : []))]);
	return topics.filter((topic) => parents.has(topic.uid)).map((topic) => topic.uid);
}

/** What a drop changes: a note gets another topic, a topic another parent (`null`: the root of the project). */
export type DropChange = { kind: "note"; uid: string; version: number; topic: string | null } | { kind: "topic"; uid: string; version: number; parent: string | null };

function descendants(topics: readonly IndexedTopic[], uid: string): Set<string> {
	const found = new Set([uid]);
	for (let grew = true; grew; ) {
		grew = false;
		for (const topic of topics) {
			if (topic.parent_uid && found.has(topic.parent_uid) && !found.has(topic.uid)) {
				found.add(topic.uid);
				grew = true;
			}
		}
	}
	return found;
}

/**
 * Where a dragged note or topic lands when it is dropped `before`, `after` or `inside` the target: inside a topic
 * it goes below it, next to a node it goes below that node's topic (or the root). `null` if the drop is not
 * allowed (another project, a note as container, an archived or system topic, a loop) or changes nothing.
 */
export function dropChange(
	topics: readonly IndexedTopic[],
	notes: readonly IndexedNote[],
	sourceId: string,
	targetId: string | null,
	position: "before" | "after" | "inside",
	projectUid?: string,
): DropChange | null {
	const topic = topics.find((entry) => entry.uid === sourceId);
	const note = notes.find((entry) => entry.uid === sourceId);
	const source = topic ?? note;
	if (!source) return null;
	let container: string | null;
	if (targetId === null) {
		container = null;
		if (projectUid && source.project_uid !== projectUid) return null;
	} else {
		const targetTopic = topics.find((entry) => entry.uid === targetId);
		const targetNote = notes.find((entry) => entry.uid === targetId);
		const target = targetTopic ?? targetNote;
		if (!target || target.project_uid !== source.project_uid || target.uid === source.uid) return null;
		if (position === "inside") {
			if (!targetTopic || targetTopic.archived) return null;
			container = targetTopic.uid;
		} else {
			container = targetTopic ? targetTopic.parent_uid : (targetNote?.topic_uid ?? null);
		}
	}
	const parent = container ? topics.find((entry) => entry.uid === container) : undefined;
	if (parent?.archived) return null;
	if (topic) {
		if (topic.system || (container && descendants(topics, topic.uid).has(container))) return null;
		return container === topic.parent_uid ? null : { kind: "topic", uid: topic.uid, version: topic.version, parent: container };
	}
	return container === note!.topic_uid ? null : { kind: "note", uid: note!.uid, version: note!.version, topic: container };
}

/** The projects with something to show, in the given order of the projects. */
export function groupByProject<T extends { uid: string }>(
	projects: readonly T[],
	topics: readonly IndexedTopic[],
	notes: readonly IndexedNote[],
): Array<{ project: T; topics: IndexedTopic[]; notes: IndexedNote[] }> {
	return projects.map((project) => ({
		project,
		topics: topics.filter((topic) => topic.project_uid === project.uid),
		notes: notes.filter((note) => note.project_uid === project.uid),
	}));
}

/** The topics a note or topic can be moved to: active, in the project, and not the topic itself or below it. */
export function targetTopics(topics: readonly IndexedTopic[], projectUid: string, exclude?: string): IndexedTopic[] {
	const blocked = exclude ? descendants(topics, exclude) : new Set<string>();
	return topics.filter((topic) => topic.project_uid === projectUid && !topic.archived && !blocked.has(topic.uid));
}
