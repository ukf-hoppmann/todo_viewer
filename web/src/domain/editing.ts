// Edit mode: a draft of the editable fields and the changes to send. Pure functions, no React.
import type { ItemFields, Schemas } from "../api/client";
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

// ---------- creating ----------

const TYPES = ["Epic", "Story", "Task"] as const;

/** Types a new item may have under `parent` (all types without a parent). */
export function childTypes(parent: Item | null): string[] {
  if (!parent) return [...TYPES];
  return TYPES.filter((t) => (PARENT_TYPES[t] ?? []).includes(parent.type));
}

export interface NewItemDraft {
  source_id: string;
  type: string;
  title: string;
  area: string;
  priority: string;
  parent: string;
  required_for_parent: "" | "Yes" | "No";
  goal: string;
  completion_criteria: string;
  summary: string;
}

/** An empty new item; a child starts with the parent's source and area, required for it. */
export function newItemDraft(sourceId: string, parent: Item | null): NewItemDraft {
  const types = childTypes(parent);
  return {
    source_id: parent?.source_id ?? sourceId,
    type: types.includes("Story") ? "Story" : (types[0] ?? "Task"),
    title: "",
    area: parent?.area ?? "",
    priority: "Normal",
    parent: parent?.id ?? "",
    required_for_parent: parent ? "Yes" : "",
    goal: "",
    completion_criteria: "",
    summary: "",
  };
}

export type CreateRequest = Schemas["ItemCreateIn"];

/** The create request: trimmed text, optional fields only when set. */
export function createRequest(draft: NewItemDraft): CreateRequest {
  const request: CreateRequest = {
    source_id: draft.source_id,
    type: draft.type,
    title: draft.title.trim(),
    area: draft.area.trim(),
    goal: draft.goal.trim(),
    completion_criteria: draft.completion_criteria.trim(),
    priority: draft.priority,
  };
  if (draft.parent) {
    request.parent = draft.parent;
    if (draft.required_for_parent) request.required_for_parent = draft.required_for_parent;
  }
  if (draft.summary.trim()) request.summary = draft.summary.trim();
  return request;
}

// ---------- trash ----------

/** Trashed items per project (alphabetical), most recently deleted first. */
export function groupTrash(items: readonly Item[]): { project: string; items: Item[] }[] {
  const byProject = new Map<string, Item[]>();
  for (const item of items) byProject.set(item.project, [...(byProject.get(item.project) ?? []), item]);
  return [...byProject.keys()].sort().map((project) => ({
    project,
    items: [...byProject.get(project)!].sort((a, b) => (b.deleted ?? "").localeCompare(a.deleted ?? "") || a.id.localeCompare(b.id)),
  }));
}

// ---------- notes and specs ----------

export interface NotesForm {
  topic: string;
  discussed: string;
  decided: string;
  open: string;
  summary: string;
}

export type NotesRequest = Schemas["NotesEntryIn"];

const bullets = (text: string) =>
  text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

/** One notes entry; each non-empty line becomes a bullet. The summary is only sent where it is asked for. */
export function notesRequest(form: NotesForm, hasSummary: boolean): NotesRequest {
  const request: NotesRequest = {
    topic: form.topic.trim(),
    discussed: bullets(form.discussed),
    decided: bullets(form.decided),
    open: bullets(form.open),
  };
  if (!hasSummary && form.summary.trim()) request.summary = form.summary.trim();
  return request;
}

/** `<ID>_spec.md`, or `<ID>_spec_<topic>.md` with the topic reduced to lowercase letters, digits and dashes. */
export function specName(itemId: string, topic: string): string {
  const slug = topic
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug ? `${itemId}_spec_${slug}.md` : `${itemId}_spec.md`;
}
