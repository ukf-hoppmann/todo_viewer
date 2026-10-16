/** Test ids of the layout plugin (scope client 7). */
export const layoutTestIds = {
	sidebar: "layout-header-sidebar.sidebar",
	headerActions: "layout-header-sidebar.header-actions",
	/** A widget in the header: `layout-header-sidebar.header-action.<owner id>.<name>` (rule 7.2). */
	headerAction: (ownerId: string, name: string) => `layout-header-sidebar.header-action.${ownerId}.${name}`,
	/** A section of the sidebar: `layout-header-sidebar.sidebar-section.<owner id>.<name>` (rule 7.2). */
	sidebarSection: (ownerId: string, name: string) => `layout-header-sidebar.sidebar-section.${ownerId}.${name}`,
} as const;
