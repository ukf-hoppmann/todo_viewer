// UI state (filters, view, selection, language). Same JSON shape as the old frontend,
// so configs/ui_state.json keeps working across the switch.
import type { Lang } from "../i18n/messages";

export const VIEWS = ["tree", "graph", "kanban", "notes", "trash"] as const;
export type View = (typeof VIEWS)[number];
export const BACKENDS = ["markdown", "database"] as const;
/** Where a project is stored: the same two values the API uses. */
export type DefaultBackend = (typeof BACKENDS)[number];
export type HiddenKind = "hiddenProjects" | "hiddenStatuses" | "hiddenPriorities";

/** A note is addressed by its project and label (labels count per project). */
export interface NoteRef {
  project: string;
  label: string;
}

export interface UiState {
  hiddenProjects: ReadonlySet<string>;
  hiddenStatuses: ReadonlySet<string>;
  hiddenPriorities: ReadonlySet<string>;
  /** Collapsed tree nodes (item uids). */
  collapsed: ReadonlySet<string>;
  /** Projects the tree's collapse buttons act on; empty means all. */
  markedProjects: ReadonlySet<string>;
  search: string;
  selectedId: string | null;
  currentView: View;
  lang: Lang;
  /** The storage a new project is preselected with. */
  defaultBackend: DefaultBackend;
  /** Notes area: the project the topic tree is limited to (null = all), the chosen topic, and the open note. */
  notesProject: string | null;
  notesTopic: NoteRef | null;
  selectedNote: NoteRef | null;
}

export const INITIAL_UI_STATE: UiState = {
  hiddenProjects: new Set(),
  hiddenStatuses: new Set(),
  hiddenPriorities: new Set(),
  collapsed: new Set(),
  markedProjects: new Set(),
  search: "",
  selectedId: null,
  currentView: "tree",
  lang: "de",
  defaultBackend: "markdown",
  notesProject: null,
  notesTopic: null,
  selectedNote: null,
};

const SET_KEYS = ["hiddenProjects", "hiddenStatuses", "hiddenPriorities", "collapsed", "markedProjects"] as const;

function stringSet(value: unknown): Set<string> | undefined {
  return Array.isArray(value) ? new Set(value.filter((v): v is string => typeof v === "string")) : undefined;
}

/** Applies whatever is valid in a stored snapshot; invalid or unknown fields are ignored. */
export function mergeStored(base: UiState, raw: unknown): UiState {
  if (typeof raw !== "object" || raw === null) return base;
  const r = raw as Record<string, unknown>;
  const next: UiState = { ...base };
  for (const key of SET_KEYS) next[key] = stringSet(r[key]) ?? base[key];
  if (typeof r.search === "string") next.search = r.search;
  if (typeof r.selectedId === "string" || r.selectedId === null) next.selectedId = r.selectedId;
  if (VIEWS.includes(r.currentView as View)) next.currentView = r.currentView as View;
  if (r.lang === "de" || r.lang === "en") next.lang = r.lang;
  if (BACKENDS.includes(r.defaultBackend as DefaultBackend)) next.defaultBackend = r.defaultBackend as DefaultBackend;
  if (typeof r.notesProject === "string" || r.notesProject === null) next.notesProject = r.notesProject;
  const ref = (value: unknown): NoteRef | null | undefined => {
    if (value === null) return null;
    const v = value as Partial<NoteRef> | undefined;
    return typeof v?.project === "string" && typeof v.label === "string" ? { project: v.project, label: v.label } : undefined;
  };
  next.notesTopic = ref(r.notesTopic) ?? next.notesTopic;
  next.selectedNote = ref(r.selectedNote) ?? next.selectedNote;
  return next;
}

export function snapshot(state: UiState): Record<string, unknown> {
  return {
    hiddenProjects: [...state.hiddenProjects],
    hiddenStatuses: [...state.hiddenStatuses],
    hiddenPriorities: [...state.hiddenPriorities],
    collapsed: [...state.collapsed],
    markedProjects: [...state.markedProjects],
    search: state.search,
    selectedId: state.selectedId,
    currentView: state.currentView,
    lang: state.lang,
    defaultBackend: state.defaultBackend,
    notesProject: state.notesProject,
    notesTopic: state.notesTopic,
    selectedNote: state.selectedNote,
  };
}

export type UiAction =
  | { type: "load"; stored: unknown }
  | { type: "toggleHidden"; kind: HiddenKind; value: string }
  | { type: "showProject"; project: string }
  | { type: "toggleCollapsed"; uid: string }
  | { type: "setCollapsed"; uids: readonly string[]; collapsed: boolean }
  | { type: "toggleMarked"; project: string }
  | { type: "search"; text: string }
  | { type: "select"; uid: string | null }
  | { type: "view"; view: View }
  | { type: "lang"; lang: Lang }
  | { type: "defaultBackend"; backend: DefaultBackend }
  | { type: "notesScope"; project: string | null; topic: NoteRef | null }
  | { type: "selectNote"; note: NoteRef | null }
  /** Jumps into the Notes area to one note (from the due list, an item, or a link). */
  | { type: "openNote"; note: NoteRef };

function toggled(set: ReadonlySet<string>, value: string): Set<string> {
  const next = new Set(set);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

export function uiReducer(state: UiState, action: UiAction): UiState {
  switch (action.type) {
    case "load":
      return mergeStored(state, action.stored);
    case "toggleHidden":
      return { ...state, [action.kind]: toggled(state[action.kind], action.value) };
    case "showProject": {
      const hiddenProjects = new Set(state.hiddenProjects);
      hiddenProjects.delete(action.project);
      return { ...state, hiddenProjects };
    }
    case "toggleCollapsed":
      return { ...state, collapsed: toggled(state.collapsed, action.uid) };
    case "setCollapsed": {
      const collapsed = new Set(state.collapsed);
      for (const uid of action.uids) {
        if (action.collapsed) collapsed.add(uid);
        else collapsed.delete(uid);
      }
      return { ...state, collapsed };
    }
    case "toggleMarked":
      return { ...state, markedProjects: toggled(state.markedProjects, action.project) };
    case "search":
      return { ...state, search: action.text };
    case "select":
      return { ...state, selectedId: action.uid };
    case "view":
      return { ...state, currentView: action.view };
    case "lang":
      return { ...state, lang: action.lang };
    case "defaultBackend":
      return { ...state, defaultBackend: action.backend };
    case "notesScope":
      return { ...state, notesProject: action.project, notesTopic: action.topic };
    case "selectNote":
      return { ...state, selectedNote: action.note };
    case "openNote":
      return { ...state, currentView: "notes", selectedNote: action.note };
  }
}
