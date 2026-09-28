// Edit mode: a draft of the editable fields and the changes to send. Pure functions, no React.
import type { ItemFields } from "../api/client";
import type { Item } from "./model";

/** Everything the edit form shows; "" means "not set" (no parent, no summary, ...). */
export interface ItemDraft {
  title: string;
  status: string;
  priority: string;
  required_for_parent: "" | "Yes" | "No";
  goal: string;
  completion_criteria: string;
  summary: string;
  area: string;
  parent: string;
  dependencies: string[];
}

export function draftOf(item: Item): ItemDraft {
  return {
    title: item.title,
    status: item.status,
    priority: item.priority ?? "",
    required_for_parent: item.required_for_parent == null ? "" : item.required_for_parent ? "Yes" : "No",
    goal: item.goal ?? "",
    completion_criteria: item.completion_criteria ?? "",
    summary: item.summary ?? "",
    area: item.area ?? "",
    parent: item.parent ?? "",
    dependencies: [...item.dependencies],
  };
}

const TEXT_FIELDS = ["title", "status", "priority", "goal", "completion_criteria", "area"] as const;

/** Only the fields that differ from the item, in the form the API expects (null clears summary/parent). */
export function changedFields(item: Item, draft: ItemDraft): Partial<ItemFields> {
  const before = draftOf(item);
  const changes: Partial<ItemFields> = {};
  for (const field of TEXT_FIELDS) {
    const value = draft[field].trim();
    if (value !== before[field]) changes[field] = value;
  }
  const summary = draft.summary.trim();
  if (summary !== before.summary) changes.summary = summary || null;
  const parent = draft.parent.trim();
  if (parent !== before.parent) changes.parent = parent || null;
  // A parented item needs "Required for parent"; it goes along with a new parent.
  if (draft.required_for_parent !== before.required_for_parent || (parent && parent !== before.parent)) {
    if (parent && draft.required_for_parent) changes.required_for_parent = draft.required_for_parent;
  }
  if (draft.dependencies.join("\n") !== before.dependencies.join("\n")) changes.dependencies = [...draft.dependencies];
  return changes;
}

/** After a conflict: fields left untouched take the newer value, own edits are kept. */
export function rebaseDraft(oldBase: Item, newBase: Item, draft: ItemDraft): ItemDraft {
  const before = draftOf(oldBase);
  const after = draftOf(newBase);
  const pick = <K extends keyof ItemDraft>(key: K): ItemDraft[K] =>
    JSON.stringify(draft[key]) === JSON.stringify(before[key]) ? after[key] : draft[key];
  return Object.fromEntries((Object.keys(draft) as (keyof ItemDraft)[]).map((k) => [k, pick(k)])) as unknown as ItemDraft;
}

const PARENT_TYPES: Record<string, readonly string[]> = { Epic: [], Story: ["Epic"], Task: ["Epic", "Story"] };

/** Possible parents: same backlog, allowed type, never the item itself or one of its descendants. */
export function parentCandidates(item: Item, items: readonly Item[]): Item[] {
  const allowed = PARENT_TYPES[item.type] ?? ["Epic", "Story"];
  const excluded = descendantUids(item, items).add(item.uid);
  return items.filter((i) => i.source_id === item.source_id && allowed.includes(i.type) && !excluded.has(i.uid));
}

/** Possible dependencies: every other item of the same backlog. */
export function dependencyCandidates(item: Item, items: readonly Item[]): Item[] {
  return items.filter((i) => i.source_id === item.source_id && i.uid !== item.uid);
}

function descendantUids(item: Item, items: readonly Item[]): Set<string> {
  const found = new Set<string>();
  let parents = new Set([item.uid]);
  while (parents.size) {
    const next = items.filter((i) => i.parentUid && parents.has(i.parentUid) && !found.has(i.uid));
    next.forEach((i) => found.add(i.uid));
    parents = new Set(next.map((i) => i.uid));
  }
  return found;
}
