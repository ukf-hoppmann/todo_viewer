// Reading a sync preview: pure functions, no React or network.
import type { Schemas } from "../api/client";

export type SyncPreview = Schemas["SyncOut"];
export type SyncDirection = NonNullable<Schemas["SyncIn"]["direction"]>;
/** How a project's mirror relates to its primary source since the last sync. */
export type SyncState = Schemas["SyncStatusOut"]["state"];
/** "sync" only copies; "switch" copies and then moves the project to the other backend. */
export type SyncMode = "sync" | "switch";

const sections = (p: SyncPreview) => [p.items, p.documents];

/** How many items and documents a sync would create, overwrite, or find missing on the target. */
export function changeCount(p: SyncPreview): number {
  return sections(p).reduce((sum, s) => sum + s.created.length + s.changed.length + s.missing.length, 0);
}

/** Entries only the target has: they stay unless the user asks to delete them. */
export function hasMissing(p: SyncPreview): boolean {
  return sections(p).some((s) => s.missing.length > 0);
}

export function isInSync(p: SyncPreview): boolean {
  return changeCount(p) === 0;
}

/** A switch needs both sides equal afterwards, so what is missing on the target has to be deleted. */
export function canRun(p: SyncPreview, mode: SyncMode, deleteMissing: boolean): boolean {
  return mode === "sync" || !hasMissing(p) || deleteMissing;
}

/** Direction of the sync that precedes a switch away from `backend`. */
export function switchDirection(backend: "markdown" | "database"): SyncDirection {
  return backend === "markdown" ? "from_md" : "to_md";
}

/** The default direction of a sync: from the primary source to its mirror. */
export function defaultDirection(primary: "markdown" | "database"): SyncDirection {
  return primary === "database" ? "to_md" : "from_md";
}

/** Whether the sidebar marks the project: the mirror changed or cannot be read, so something is left to do. */
export function needsAttention(state: SyncState): boolean {
  return state === "mirror_changed" || state === "both_changed" || state === "unreadable";
}
