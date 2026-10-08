// The list of due notes and the notices on notes and items. Pure functions, no React, no DOM, no network.
import type { Schemas } from "../api/client";

export type DueNote = Schemas["DueNoteOut"];
export type Notice = Schemas["todo_viewer__api__v2__notes_schemas__NoticeOut"];
export type LinkedNote = Schemas["LinkedNoteOut"];

/** The reasons a note is due, in the order the list shows them. */
export const REASON_ORDER = ["trigger", "notice", "topic_due", "review_expired"] as const;
export type DueReason = (typeof REASON_ORDER)[number];

export interface DueGroup {
  reason: DueReason;
  notes: DueNote[];
}

/** The key of a note in lists and for focus: labels count per project. */
export const rowKey = (note: { project: string; label: string }) => `${note.project}/${note.label}`;

const reasonOf = (note: DueNote): DueReason => (REASON_ORDER as readonly string[]).includes(note.reason ?? "") ? (note.reason as DueReason) : "review_expired";

/** The due notes in groups by reason, in the fixed order of `REASON_ORDER`. Empty groups are left out, the order within
 *  a group is the order of the list. */
export function groupDueByReason(notes: readonly DueNote[]): DueGroup[] {
  return REASON_ORDER.map((reason) => ({ reason, notes: notes.filter((n) => reasonOf(n) === reason) })).filter((g) => g.notes.length > 0);
}

export type RowAction = "snooze" | "done" | "dropped" | "promote" | "keep" | "detach" | "drop" | "open";

const NOTE_ORDER: readonly RowAction[] = ["snooze", "done", "dropped", "promote", "keep", "open"];
const NOTICE_ORDER: readonly RowAction[] = ["keep", "detach", "drop", "promote", "open"];

/** What a row offers: what the server allows for the note (a notice is decided with keep, detach, drop and promote;
 *  other notes can be snoozed, closed and kept), plus promoting a note that is not a notice, plus opening it. */
export function rowActions(note: DueNote): RowAction[] {
  const allowed = new Set<string>(note.actions);
  allowed.add("open");
  if (reasonOf(note) !== "notice") allowed.add("promote");
  return (reasonOf(note) === "notice" ? NOTICE_ORDER : NOTE_ORDER).filter((a) => allowed.has(a));
}

/** The row to focus after the acted one is gone: the one that followed, else the one before; null if none is left. */
export function nextAfterAction(keys: readonly string[], acted: string): string | null {
  const at = keys.indexOf(acted);
  if (at < 0) return null;
  return keys[at + 1] ?? keys[at - 1] ?? null;
}

const KNOWN_CAUSES = ["item_completed", "item_rejected", "item_deleted", "item_retyped", "project_unreachable", "note_dropped", "note_promoted"] as const;

export interface NoticeText {
  key: `notice.${(typeof KNOWN_CAUSES)[number]}` | "notice.unknown";
  params: { other: string };
}

/** What a notice says: a message key and the other end of the link as "Project · Label". */
export function describeNotice(notice: Notice): NoticeText {
  const other = `${notice.counterpart.project} · ${notice.counterpart.label}`;
  const known = (KNOWN_CAUSES as readonly string[]).includes(notice.cause);
  return { key: known ? (`notice.${notice.cause}` as NoticeText["key"]) : "notice.unknown", params: { other } };
}

const CLOSED_NOTE = new Set(["done", "dropped", "promoted"]);

/** The notes that point at an item: open ones first, then closed ones; the order within each stays. */
export function sortLinkedNotes(notes: readonly LinkedNote[]): LinkedNote[] {
  return [...notes.filter((n) => !CLOSED_NOTE.has(n.status)), ...notes.filter((n) => CLOSED_NOTE.has(n.status))];
}
