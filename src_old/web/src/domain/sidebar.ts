// The sidebar is a shell: search and projects are always there, the tab decides which filter sections follow.

/** A filter section below search and projects. */
export type SidebarSection = "itemStatus" | "itemPriority" | "noteStatus";

/** The tabs, as `state/uiState` names them. */
type Tab = "tree" | "graph" | "kanban" | "notes" | "trash";

const SECTIONS: Record<Tab, readonly SidebarSection[]> = {
  tree: ["itemStatus", "itemPriority"],
  graph: ["itemStatus", "itemPriority"],
  kanban: ["itemStatus", "itemPriority"],
  notes: ["noteStatus"],
  trash: [],
};

export function sidebarSections(tab: Tab): readonly SidebarSection[] {
  return SECTIONS[tab];
}
