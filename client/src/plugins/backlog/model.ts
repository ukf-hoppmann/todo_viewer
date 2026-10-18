import type { DropPosition, FlatNode } from "../../shared";
import { priorityColor, statusColor } from "./constants";
import type { IndexItem } from "./api";

export interface Filters {
	hiddenStatuses: ReadonlySet<string>;
	hiddenPriorities: ReadonlySet<string>;
	search: string;
}

/** The items the filters let through. Hidden values are stored (not shown ones), so new values are visible. */
export function filterItems(items: readonly IndexItem[], filters: Filters): IndexItem[] {
	const query = filters.search.trim().toLowerCase();
	return items.filter(
		(item) =>
			!filters.hiddenStatuses.has(item.status) &&
			!filters.hiddenPriorities.has(item.priority) &&
			(!query || item.title.toLowerCase().includes(query) || item.label.toLowerCase().includes(query)),
	);
}

export interface Progress {
	done: number;
	total: number;
}

/** Progress of a project over all its items (filters do not matter); optional and rejected items do not count. */
export function projectProgress(items: readonly IndexItem[]): Progress {
	const counted = items.filter((item) => item.required_for_parent !== false && item.status !== "Rejected");
	return { done: counted.filter((item) => item.status === "Completed").length, total: counted.length };
}

/** The projects with items, in the given order of the projects; each with its visible items in server order. */
export function groupByProject<T extends { uid: string }>(
	projects: readonly T[],
	items: readonly IndexItem[],
): Array<{ project: T; items: IndexItem[] }> {
	return projects
		.map((project) => ({ project, items: items.filter((item) => item.project_uid === project.uid) }))
		.filter((group) => group.items.length > 0);
}

/**
 * The nodes for the shared tree view; an item whose parent is filtered out becomes a root. With the extended marking
 * a root starts an area and an item below it a nested one; a task belongs to the area of its story.
 */
export function toFlatNodes(items: readonly IndexItem[], extendedMarking = false): FlatNode[] {
	const byUid = new Map(items.map((item) => [item.uid, item]));
	const isRoot = (item: IndexItem) => !item.parent_uid || !byUid.has(item.parent_uid);
	const areaOf = (item: IndexItem): 1 | 2 | undefined => {
		if (!extendedMarking) return undefined;
		if (isRoot(item)) return 1;
		const parent = byUid.get(item.parent_uid!)!;
		return item.type === "Task" && isRoot(parent) ? 1 : 2;
	};
	return items.map((item) => ({
		area: areaOf(item),
		id: item.uid,
		parentId: item.parent_uid,
		label: item.title,
		badge: item.label,
		statusColor: statusColor(item.status),
		dashed: item.parent_uid !== null && item.required_for_parent === false,
		progress: item.progress ?? undefined,
	}));
}

/** The ids of the items of one type that have children (over all items, so filtered ones stay folded when shown again). */
export function collapsibleIds(items: readonly IndexItem[], type: string, projects: ReadonlySet<string>): string[] {
	const parents = new Set(items.flatMap((item) => (item.parent_uid ? [item.parent_uid] : [])));
	return items.filter((item) => item.type === type && parents.has(item.uid) && (projects.size === 0 || projects.has(item.project_uid))).map((item) => item.uid);
}

export { priorityColor, statusColor };

export interface Placement {
	parent: string | null;
	position: number;
}

/**
 * Where a dragged item lands: below the target (`inside`, at the end) or next to it (`before`, `after`, under the
 * target's parent). The position counts among the siblings without the dragged item, as the server does. `null`
 * if the structure forbids it: an epic stays a root, a task has no children.
 */
export function placementOf(items: readonly IndexItem[], sourceUid: string, targetUid: string, position: DropPosition): Placement | null {
	const source = items.find((item) => item.uid === sourceUid);
	const target = items.find((item) => item.uid === targetUid);
	if (!source || !target || source.uid === target.uid) return null;
	const parent = position === "inside" ? target.uid : target.parent_uid;
	if (position === "inside" && target.type === "Task") return null;
	if (parent !== null && source.type === "Epic") return null;
	const siblings = items.filter((item) => item.project_uid === target.project_uid && item.parent_uid === parent && item.uid !== source.uid);
	if (position === "inside") return { parent, position: siblings.length };
	const index = siblings.findIndex((item) => item.uid === target.uid);
	return { parent, position: position === "before" ? index : index + 1 };
}
