// Reading a sync preview: pure functions, no React or network.
import type { Schemas } from "../api/client";

export type SyncPreview = Schemas["SyncOut"];
export type SyncDirection = NonNullable<Schemas["SyncIn"]["direction"]>;
/** How a project's mirror relates to its primary source since the last sync. */
export type SyncState = Schemas["SyncStatusOut"]["state"];
/** "sync" only copies; "switch" copies and then moves the project to the other backend. */
export type SyncMode = "sync" | "switch";

const sections = (p: SyncPreview) => [p.items, p.documents];

/** How many items and documents a sync would carry over: new on one side or changed on one side only. */
export function changeCount(p: SyncPreview): number {
  return sections(p).reduce((sum, s) => sum + s.created.length + s.changed.length, 0);
}

/** Entries that need a decision: nothing of them is touched until the owner decides. */
export function conflictCount(p: SyncPreview): number {
  return p.conflicts.length;
}

export function isInSync(p: SyncPreview): boolean {
  return changeCount(p) === 0 && conflictCount(p) === 0;
}

/** A switch needs both sides equal afterwards, so it waits for the conflicts to be decided. */
export function canRun(p: SyncPreview, mode: SyncMode): boolean {
  return mode === "sync" || conflictCount(p) === 0;
}

/** Which side(s) a run may write: both (each entry travels from the side that changed it) or only one. */
export type SyncScope = SyncDirection | "both";

/** The `direction` of the request: null lets the sync run in both directions. */
export function directionOf(scope: SyncScope): SyncDirection | null {
  return scope === "both" ? null : scope;
}

/** Direction of the sync that precedes a switch away from `backend`. */
export function switchDirection(backend: "markdown" | "database"): SyncDirection {
  return backend === "markdown" ? "from_md" : "to_md";
}

/** Whether the sidebar marks the project: the mirror changed or cannot be read, so something is left to do. */
export function needsAttention(state: SyncState): boolean {
  return state === "mirror_changed" || state === "both_changed" || state === "unreadable";
}

export type SyncConflict = Schemas["SyncConflictOut"];
export type ConflictChoice = Schemas["ResolutionIn"]["choice"];
/** The decision per conflict, by `conflictKey`; a conflict without an entry is deferred. */
export type ConflictChoices = Readonly<Record<string, ConflictChoice>>;

export function conflictKey(c: Pick<SyncConflict, "kind" | "label" | "name">): string {
  return `${c.kind}/${c.label}/${c.name ?? ""}`;
}

export function choiceOf(choices: ConflictChoices, c: SyncConflict): ConflictChoice {
  return choices[conflictKey(c)] ?? "defer";
}

/** The `resolutions` of the request: only what was decided; everything else is deferred by the server. */
export function buildResolutions(conflicts: readonly SyncConflict[], choices: ConflictChoices): Schemas["ResolutionIn"][] {
  return conflicts.flatMap((c) => {
    const choice = choiceOf(choices, c);
    return choice === "defer" ? [] : [{ kind: c.kind, label: c.label, name: c.name, choice }];
  });
}

/** The fields of an item conflict in which the two versions differ (all of them if a side is missing). */
export function changedFields(c: SyncConflict): { name: string; database: string | null; markdown: string | null }[] {
  const database = new Map((c.database?.fields ?? []).map((f) => [f.name, f.value]));
  const markdown = new Map((c.markdown?.fields ?? []).map((f) => [f.name, f.value]));
  const names = [...new Set([...database.keys(), ...markdown.keys()])];
  return names
    .map((name) => ({ name, database: database.get(name) ?? null, markdown: markdown.get(name) ?? null }))
    .filter((f) => f.database !== f.markdown || !c.database || !c.markdown);
}
