// Promoting a note to a backlog item: the form's draft and the request. Pure functions, no React.
import type { Schemas } from "../api/client";
import { childTypes } from "./editing";
import type { Item } from "./model";

/** Everything the promote form shows; "" means "not set". */
export interface PromoteDraft {
  item_type: "Epic" | "Story" | "Task";
  title: string;
  summary: string;
  area: string;
  goal: string;
  completion_criteria: string;
  priority: string;
  parent: string;
  required_for_parent: "" | "Yes" | "No";
}

/** Title and summary start as the note's summary, the goal as its long text (or the summary if there is none). */
export function promoteDraft(note: { summary: string; body: string | null }): PromoteDraft {
  const body = note.body?.trim() ?? "";
  return {
    item_type: "Story",
    title: note.summary,
    summary: note.summary,
    area: "",
    goal: body === "" ? note.summary : body,
    completion_criteria: "",
    priority: "Normal",
    parent: "",
    required_for_parent: "",
  };
}

export type PromoteRequest = Schemas["PromoteIn"];

/** The request: trimmed text; title and summary only when set (the server takes them from the note otherwise);
 *  a parent comes with its "required for parent". */
export function promoteRequest(draft: PromoteDraft, version: string): PromoteRequest {
  const request: PromoteRequest = {
    version,
    item_type: draft.item_type,
    area: draft.area.trim(),
    goal: draft.goal.trim(),
    completion_criteria: draft.completion_criteria.trim(),
    priority: draft.priority,
  };
  if (draft.title.trim()) request.title = draft.title.trim();
  if (draft.summary.trim()) request.summary = draft.summary.trim();
  if (draft.parent) {
    request.parent = draft.parent;
    if (draft.required_for_parent) request.required_for_parent = draft.required_for_parent;
  }
  return request;
}

const CLOSED = new Set(["Completed", "Rejected"]);

/** The open items of a project that can be the parent of an item of `type`. */
export function parentCandidates(items: readonly Item[], project: string, type: string): Item[] {
  return items.filter((i) => i.project === project && !CLOSED.has(i.status) && childTypes(i).includes(type));
}
