// What the card of a project says and offers: pure functions, no React or network.
import type { Schemas } from "../api/client";
import { needsAttention, type SyncState } from "./sync";

/** The fields of a project that decide what its card shows. */
export type ProjectSource = Pick<Schemas["SourceStatusOut"], "primary" | "mirror" | "markdown_path" | "auto_sync">;
/** The last known sync state of a project, if it has been asked for yet. */
export type ProjectStatus = { state: SyncState; conflicts: number };

/** How loud the status is: "attention" wants the owner, "pending" is a difference that is not a problem. */
export type ProjectTone = "loading" | "idle" | "ok" | "pending" | "attention";
/**
 * The one thing the card puts forward. "resolve" and "sync" open the sync dialog; "enableMirror" switches an existing
 * mirror setup on; "setupMirror" asks for the markdown folder the mirror needs first.
 */
export type ProjectAction = "sync" | "resolve" | "enableMirror" | "setupMirror";

/** The three states of a mirror: none, one that is synced by hand, one the viewer syncs by itself. */
export type MirrorMode = "off" | "manual" | "auto";
export const MIRROR_MODES: readonly MirrorMode[] = ["off", "manual", "auto"];

/** What a change to `mode` sets: whether a mirror is kept and the automatic sync with it; both go in one request. */
export function mirrorSettings(mode: MirrorMode): { mirror: boolean; autoSync: boolean } {
  return { mirror: mode !== "off", autoSync: mode === "auto" };
}

/** Whether the viewer syncs the project by itself: the switch is on and there is a mirror for it to act on. */
export function autoSyncOn(source: Pick<ProjectSource, "mirror" | "auto_sync">): boolean {
  return source.mirror !== "none" && source.auto_sync;
}

export interface ProjectView {
  /** The state to name; "loading" while it is unknown. Open conflicts win over what the state says. */
  status: SyncState | "loading";
  tone: ProjectTone;
  conflicts: number;
  hasMirror: boolean;
  /** A database project whose markdown folder is kept although the mirror is off. */
  mirrorOff: boolean;
  action: ProjectAction;
  /** A database project without a markdown folder has nowhere to go to. */
  switchBlocked: boolean;
  /** The mirror's state from the project itself; a switch left on without a mirror counts as off, it does nothing. */
  mirrorMode: MirrorMode;
  /** A mirror can be switched on: a database project needs a markdown folder for it. */
  canMirror: boolean;
}

const toneOf = (state: SyncState, conflicts: number): ProjectTone => {
  if (needsAttention(state, conflicts)) return "attention";
  if (state === "in_sync") return "ok";
  if (state === "none") return "idle";
  return "pending";
};

function actionOf(hasMirror: boolean, conflicts: number, source: ProjectSource): ProjectAction {
  if (!hasMirror) return source.primary === "database" && !source.markdown_path ? "setupMirror" : "enableMirror";
  return conflicts > 0 ? "resolve" : "sync";
}

export function describeProject(source: ProjectSource, status: ProjectStatus | undefined): ProjectView {
  const hasMirror = source.mirror !== "none";
  const conflicts = status?.conflicts ?? 0;
  const known = status ? (conflicts > 0 ? "conflicts" : status.state) : "loading";
  return {
    status: known,
    tone: status ? toneOf(status.state, conflicts) : "loading",
    conflicts,
    hasMirror,
    mirrorOff: source.primary === "database" && !hasMirror && !!source.markdown_path,
    action: actionOf(hasMirror, conflicts, source),
    switchBlocked: source.primary === "database" && !source.markdown_path,
    mirrorMode: !hasMirror ? "off" : autoSyncOn(source) ? "auto" : "manual",
    canMirror: source.primary === "markdown" || !!source.markdown_path,
  };
}
