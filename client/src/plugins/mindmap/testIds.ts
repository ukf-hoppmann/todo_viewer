/** Test ids of the mindmap plugin. `id` is the `uid` of a node, for the root the `uid` of the project. */
export const mindmapTestIds = {
	page: "mindmap.page",
	chooseProject: "mindmap.choose-project",
	map: "mindmap.map",
	error: "mindmap.error",
	node: (id: string) => `mindmap.node.${id}`,
	titleInput: (id: string) => `mindmap.title-input.${id}`,
	toggle: (id: string) => `mindmap.toggle.${id}`,
	add: (id: string) => `mindmap.add.${id}`,
	remove: (id: string) => `mindmap.remove.${id}`,
	detail: "mindmap.detail",
} as const;
