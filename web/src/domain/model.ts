// Frontend view of the backlog: pure functions, no React, no fetching.
import type { ApiItem, SourceStatus } from "../api/client";

export const STATUS_KEYS = ["Open", "In progress", "Awaiting confirmation", "Completed", "Rejected"] as const;
export const PRIORITY_KEYS = ["Urgent", "Important", "Prospective"] as const;
export const TERMINAL_STATUSES: ReadonlySet<string> = new Set(["Completed", "Rejected"]);
export const CHECKBOX_STATUSES = ["Open", "Completed"] as const;

/** Parent/dependency references are item ids within the same project, so project::id identifies an item. */
export type Uid = string;

export interface Item extends ApiItem {
  uid: Uid;
  parentUid: Uid | null;
  dependencyUids: Uid[];
}

export function uidOf(project: string, id: string): Uid {
  return `${project}::${id}`;
}

export function toItems(apiItems: readonly ApiItem[]): Item[] {
  return apiItems.map((i) => ({
    ...i,
    uid: uidOf(i.project, i.ref.id),
    parentUid: i.parent ? uidOf(i.project, i.parent) : null,
    dependencyUids: i.dependencies.map((d) => uidOf(i.project, d)),
  }));
}

export function indexByUid(items: readonly Item[]): Map<Uid, Item> {
  return new Map(items.map((i) => [i.uid, i]));
}

/** Known keys first (in their order), unknown values alphabetically after them. */
export function sortByKeyOrder(values: Iterable<string>, order: readonly string[]): string[] {
  return [...values].sort((a, b) => {
    const ia = order.indexOf(a);
    const ib = order.indexOf(b);
    if (ia !== -1 || ib !== -1) return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    return a.localeCompare(b);
  });
}

// ---------- filtering ----------

/** Filters store what is hidden, so values that appear later are visible by default. */
export interface Filters {
  hiddenProjects: ReadonlySet<string>;
  hiddenStatuses: ReadonlySet<string>;
  hiddenPriorities: ReadonlySet<string>;
  search: string;
}

export function filterItems(items: readonly Item[], f: Filters): Item[] {
  const q = f.search.trim().toLowerCase();
  return items.filter(
    (i) =>
      !f.hiddenProjects.has(i.project) &&
      !f.hiddenStatuses.has(i.status) &&
      (i.priority == null || !f.hiddenPriorities.has(i.priority)) &&
      (!q || i.title.toLowerCase().includes(q) || i.ref.id.toLowerCase().includes(q)),
  );
}

export interface FilterOptions {
  projects: string[];
  statuses: string[];
  priorities: string[];
}

export function filterOptions(items: readonly Item[], sources: readonly SourceStatus[]): FilterOptions {
  return {
    projects: [...new Set([...sources.map((s) => s.project), ...items.map((i) => i.project)])].sort(),
    statuses: sortByKeyOrder(new Set(items.map((i) => i.status)), STATUS_KEYS),
    priorities: sortByKeyOrder(new Set(items.flatMap((i) => (i.priority ? [i.priority] : []))), PRIORITY_KEYS),
  };
}

// ---------- tree ----------

export interface TreeNode {
  item: Item;
  /** Required for parent: No — drawn dashed and dimmed, not counted for progress. */
  optional: boolean;
  children: TreeNode[];
}

export interface ProjectTree {
  project: string;
  progress: Progress;
  roots: TreeNode[];
}

export interface Progress {
  done: number;
  total: number;
}

/**
 * Progress of a project over all its items, independent of the filters.
 * Optional children never block their parent and do not count.
 */
export function projectProgress(allItems: readonly Item[], project: string): Progress {
  const counted = allItems.filter((i) => i.project === project && i.required_for_parent !== false);
  return { done: counted.filter((i) => i.status === "Completed").length, total: counted.length };
}

/** Groups the visible items by project; items whose parent is hidden become roots. */
export function buildTrees(visible: readonly Item[], allItems: readonly Item[]): ProjectTree[] {
  const byProject = new Map<string, Item[]>();
  for (const item of visible) byProject.set(item.project, [...(byProject.get(item.project) ?? []), item]);

  return [...byProject.keys()].sort().map((project) => {
    const items = byProject.get(project) ?? [];
    const uids = new Set(items.map((i) => i.uid));
    const byParent = new Map<Uid | null, Item[]>();
    for (const item of items) {
      const parent = item.parentUid && uids.has(item.parentUid) ? item.parentUid : null;
      byParent.set(parent, [...(byParent.get(parent) ?? []), item]);
    }
    const level = (parent: Uid | null): TreeNode[] =>
      (byParent.get(parent) ?? []).map((item) => ({
        item,
        optional: parent !== null && item.required_for_parent === false,
        children: level(item.uid),
      }));
    return { project, progress: projectProgress(allItems, project), roots: level(null) };
  });
}

// ---------- kanban / graph ----------

export function groupByStatus(items: readonly Item[]): { status: string; items: Item[] }[] {
  const byStatus = new Map<string, Item[]>();
  for (const item of items) byStatus.set(item.status, [...(byStatus.get(item.status) ?? []), item]);
  return sortByKeyOrder(byStatus.keys(), STATUS_KEYS).map((status) => ({ status, items: byStatus.get(status) ?? [] }));
}

export interface DependencyGraph {
  nodes: Item[];
  edges: { from: Uid; to: Uid }[];
}

/** Only items that take part in at least one visible dependency; edges point from dependency to dependent. */
export function dependencyGraph(visible: readonly Item[]): DependencyGraph {
  const uids = new Set(visible.map((i) => i.uid));
  const edges = visible.flatMap((i) => i.dependencyUids.filter((d) => uids.has(d)).map((d) => ({ from: d, to: i.uid })));
  const connected = new Set(edges.flatMap((e) => [e.from, e.to]));
  return { nodes: visible.filter((i) => connected.has(i.uid)), edges };
}

// ---------- editing ----------

export function statusOptions(item: Item): string[] {
  const options: string[] = item.format === "checkbox" ? [...CHECKBOX_STATUSES] : [...STATUS_KEYS];
  if (item.status && !options.includes(item.status)) options.push(item.status);
  return options;
}

export function priorityOptions(item: Item): string[] {
  const options: string[] = [...PRIORITY_KEYS];
  if (item.priority && !options.includes(item.priority)) options.push(item.priority);
  return options;
}

export function needsResolution(item: Item, status: string): boolean {
  return item.archive_supported && TERMINAL_STATUSES.has(status);
}

// Follows the harness convention (English, independent of the UI language).
const RESOLUTION_DEFAULTS: Record<string, string> = {
  Completed: "Confirmed by the project owner on {date}.",
  Rejected: "Rejected by the project owner on {date}.",
};

export function defaultResolution(status: string, today: Date = new Date()): string {
  return (RESOLUTION_DEFAULTS[status] ?? "").replace("{date}", today.toISOString().slice(0, 10));
}
