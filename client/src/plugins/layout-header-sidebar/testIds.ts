/** Test ids of the layout plugin (scope client 7). */
export const layoutTestIds = {
	headerActions: "layout-header-sidebar.header-actions",
	/** A widget in the header: `layout-header-sidebar.header-action.<owner id>.<name>` (rule 7.2). */
	headerAction: (ownerId: string, name: string) => `layout-header-sidebar.header-action.${ownerId}.${name}`,
} as const;
