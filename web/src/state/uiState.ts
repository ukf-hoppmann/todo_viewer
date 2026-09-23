// UI state (filters, view, selection, language). Same JSON shape as the old frontend,
// so configs/ui_state.json keeps working across the switch.
import type { Lang } from "../i18n/messages";

export const VIEWS = ["tree", "graph", "kanban"] as const;
export type View = (typeof VIEWS)[number];
export type HiddenKind = "hiddenProjects" | "hiddenStatuses" | "hiddenPriorities";

export interface UiState {
  hiddenProjects: ReadonlySet<string>;
  hiddenStatuses: ReadonlySet<string>;
  hiddenPriorities: ReadonlySet<string>;
  /** Collapsed tree nodes (item uids). */
  collapsed: ReadonlySet<string>;
  search: string;
  selectedId: string | null;
  currentView: View;
  lang: Lang;
}

export const INITIAL_UI_STATE: UiState = {
  hiddenProjects: new Set(),
  hiddenStatuses: new Set(),
  hiddenPriorities: new Set(),
  collapsed: new Set(),
  search: "",
  selectedId: null,
  currentView: "tree",
  lang: "de",
};

const SET_KEYS = ["hiddenProjects", "hiddenStatuses", "hiddenPriorities", "collapsed"] as const;

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
  return next;
}

export function snapshot(state: UiState): Record<string, unknown> {
  return {
    hiddenProjects: [...state.hiddenProjects],
    hiddenStatuses: [...state.hiddenStatuses],
    hiddenPriorities: [...state.hiddenPriorities],
    collapsed: [...state.collapsed],
    search: state.search,
    selectedId: state.selectedId,
    currentView: state.currentView,
    lang: state.lang,
  };
}

export type UiAction =
  | { type: "load"; stored: unknown }
  | { type: "toggleHidden"; kind: HiddenKind; value: string }
  | { type: "showProject"; project: string }
  | { type: "toggleCollapsed"; uid: string }
  | { type: "search"; text: string }
  | { type: "select"; uid: string | null }
  | { type: "view"; view: View }
  | { type: "lang"; lang: Lang };

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
    case "search":
      return { ...state, search: action.text };
    case "select":
      return { ...state, selectedId: action.uid };
    case "view":
      return { ...state, currentView: action.view };
    case "lang":
      return { ...state, lang: action.lang };
  }
}
