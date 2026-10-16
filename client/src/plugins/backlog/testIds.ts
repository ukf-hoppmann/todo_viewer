/** Test ids of the backlog plugin (scope client 7). */
export const backlogTestIds = {
	page: "backlog.page",
	empty: "backlog.empty",
	project: (uid: string) => `backlog.project.${uid}`,
	projectProgress: (uid: string) => `backlog.project-progress.${uid}`,
	collapse: (type: string) => `backlog.collapse.${type}`,
	statusFilter: "backlog.status-filter",
	priorityFilter: "backlog.priority-filter",
	detail: "backlog.detail",
	detailEmpty: "backlog.detail-empty",
	field: (name: string) => `backlog.field.${name}`,
	child: (uid: string) => `backlog.child.${uid}`,
	dependency: (uid: string) => `backlog.dependency.${uid}`,
	parent: "backlog.parent",
} as const;
