import type { FlatNode } from "../../shared";
import type { DueMemoOut, IndexedMemo, IndexedTopic } from "./api";
import { statusColor } from "./constants";

/**
 * The parts of a due memo for the list of due things of `workspace`: key, project, since when (the review date if the
 * server gave none), title, and the reason (translated by the caller) with the topic path.
 */
export function attentionOf(memo: DueMemoOut, reason: string): { key: string; projectUid: string; dueSince: string; title: string; caption: string } {
	const dueSince = memo.due_since ?? memo.review_at ?? "";
	const caption = [reason, memo.path.join(" › ")].filter((part) => part !== "").join(" · ");
	return { key: `memos:${memo.uid}`, projectUid: memo.project_uid, dueSince, title: `${memo.label} — ${memo.summary}`, caption };
}

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

function matches(memo: IndexedMemo, query: string): boolean {
	return !query || memo.summary.toLowerCase().includes(query) || memo.label.toLowerCase().includes(query);
}

/** The memos the filters let through: status shown, text found, and not inside a hidden topic. */
export function filterMemos(memos: readonly IndexedMemo[], topics: readonly IndexedTopic[], filters: Filters): IndexedMemo[] {
	const query = filters.search.trim().toLowerCase();
	const hidden = hiddenTopics(topics, filters.showArchivedTopics);
	return memos.filter((memo) => filters.shownStatuses.has(memo.status) && matches(memo, query) && !(memo.topic_uid && hidden.has(memo.topic_uid)));
}

/** The topics to show: not hidden; with a search only those whose name matches or that lead to a found memo. */
export function filterTopics(topics: readonly IndexedTopic[], shownMemos: readonly IndexedMemo[], filters: Filters): IndexedTopic[] {
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
	for (const memo of shownMemos) keepWithPath(memo.topic_uid);
	return visible.filter((topic) => keep.has(topic.uid));
}

/** How deep a topic stands (a root topic has depth 1). */
function depthOf(topic: IndexedTopic, byUid: ReadonlyMap<string, IndexedTopic>): number {
	let depth = 1;
	for (let current = topic; current.parent_uid && byUid.has(current.parent_uid) && depth < 50; depth++) current = byUid.get(current.parent_uid)!;
	return depth;
}

/**
 * The nodes of the shared tree for one project: topics (with the number of shown memos below them and, if the
 * extended marking is on, the area of the topics of the first two levels) and memos. Siblings: those with due
 * memos first, topics before memos, then by label.
 */
export function toFlatNodes(topics: readonly IndexedTopic[], memos: readonly IndexedMemo[], extendedMarking: boolean): FlatNode[] {
	const byUid = new Map(topics.map((topic) => [topic.uid, topic]));
	const counts = new Map<string, number>();
	for (const memo of memos) {
		for (let current = memo.topic_uid ? byUid.get(memo.topic_uid) : undefined, guard = 0; current && guard < 50; guard++) {
			counts.set(current.uid, (counts.get(current.uid) ?? 0) + 1);
			current = current.parent_uid ? byUid.get(current.parent_uid) : undefined;
		}
	}
	// Topics of the first level start an area, those of the second a nested one; deeper ones belong to the latter.
	const areaOf = (topic: IndexedTopic): 1 | 2 | undefined => (extendedMarking ? (depthOf(topic, byUid) <= 1 ? 1 : 2) : undefined);
	const dueFirst = (hasDue: boolean) => (hasDue ? 0 : 1);
	const topicNodes = topics.map((topic) => ({
		order: [dueFirst(topic.due_memos > 0), 0, topic.label] as const,
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
	const memoNodes = memos.map((memo) => {
		const topic = memo.topic_uid ? byUid.get(memo.topic_uid) : undefined;
		return {
			order: [dueFirst(memo.status === "due"), 1, memo.label] as const,
			node: {
				id: memo.uid,
				parentId: topic ? topic.uid : null,
				label: memo.summary,
				badge: memo.label,
				tag: "Memo",
				tagColor: statusColor(memo.status),
				statusColor: statusColor(memo.status),
				area: topic ? areaOf(topic) : undefined,
				dashed: memo.archived,
			} satisfies FlatNode,
		};
	});
	return [...topicNodes, ...memoNodes]
		.sort((a, b) => a.order[0] - b.order[0] || a.order[1] - b.order[1] || a.order[2].localeCompare(b.order[2], undefined, { numeric: true }))
		.map((entry) => entry.node);
}

/** The uids of all topics (they can be folded). */
export function collapsibleIds(topics: readonly IndexedTopic[], memos: readonly IndexedMemo[]): string[] {
	const parents = new Set([...topics.flatMap((t) => (t.parent_uid ? [t.parent_uid] : [])), ...memos.flatMap((n) => (n.topic_uid ? [n.topic_uid] : []))]);
	return topics.filter((topic) => parents.has(topic.uid)).map((topic) => topic.uid);
}

/** What a drop changes: a memo gets another topic, a topic another parent (`null`: the root of the project). */
export type DropChange = { kind: "memo"; uid: string; version: number; topic: string | null } | { kind: "topic"; uid: string; version: number; parent: string | null };

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
 * Where a dragged memo or topic lands when it is dropped `before`, `after` or `inside` the target: inside a topic
 * it goes below it, next to a node it goes below that node's topic (or the root). `null` if the drop is not
 * allowed (another project, a memo as container, an archived or system topic, a loop) or changes nothing.
 */
export function dropChange(
	topics: readonly IndexedTopic[],
	memos: readonly IndexedMemo[],
	sourceId: string,
	targetId: string | null,
	position: "before" | "after" | "inside",
	projectUid?: string,
): DropChange | null {
	const topic = topics.find((entry) => entry.uid === sourceId);
	const memo = memos.find((entry) => entry.uid === sourceId);
	const source = topic ?? memo;
	if (!source) return null;
	let container: string | null;
	if (targetId === null) {
		container = null;
		if (projectUid && source.project_uid !== projectUid) return null;
	} else {
		const targetTopic = topics.find((entry) => entry.uid === targetId);
		const targetMemo = memos.find((entry) => entry.uid === targetId);
		const target = targetTopic ?? targetMemo;
		if (!target || target.project_uid !== source.project_uid || target.uid === source.uid) return null;
		if (position === "inside") {
			if (!targetTopic || targetTopic.archived) return null;
			container = targetTopic.uid;
		} else {
			container = targetTopic ? targetTopic.parent_uid : (targetMemo?.topic_uid ?? null);
		}
	}
	const parent = container ? topics.find((entry) => entry.uid === container) : undefined;
	if (parent?.archived) return null;
	if (topic) {
		if (topic.system || (container && descendants(topics, topic.uid).has(container))) return null;
		return container === topic.parent_uid ? null : { kind: "topic", uid: topic.uid, version: topic.version, parent: container };
	}
	return container === memo!.topic_uid ? null : { kind: "memo", uid: memo!.uid, version: memo!.version, topic: container };
}

/** The projects with something to show, in the given order of the projects. */
export function groupByProject<T extends { uid: string }>(
	projects: readonly T[],
	topics: readonly IndexedTopic[],
	memos: readonly IndexedMemo[],
): Array<{ project: T; topics: IndexedTopic[]; memos: IndexedMemo[] }> {
	return projects.map((project) => ({
		project,
		topics: topics.filter((topic) => topic.project_uid === project.uid),
		memos: memos.filter((memo) => memo.project_uid === project.uid),
	}));
}

/** The topics a memo or topic can be moved to: active, in the project, and not the topic itself or below it. */
export function targetTopics(topics: readonly IndexedTopic[], projectUid: string, exclude?: string): IndexedTopic[] {
	const blocked = exclude ? descendants(topics, exclude) : new Set<string>();
	return topics.filter((topic) => topic.project_uid === projectUid && !topic.archived && !blocked.has(topic.uid));
}
