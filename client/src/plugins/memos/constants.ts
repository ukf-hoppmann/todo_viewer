/** The memo statuses in the order of the filter; `due` is derived by the server from the review date. */
export const STATUSES = ["waiting", "due", "snoozed", "done", "dropped", "promoted"] as const;
/** Shown by default: the open ones. */
export const DEFAULT_SHOWN_STATUSES: readonly string[] = ["waiting", "due", "snoozed"];
export const FINISHED_STATUSES: readonly string[] = ["done", "dropped", "promoted"];

export const STATUS_COLORS: Record<string, string> = {
	waiting: "#6b7280",
	due: "#d5544a",
	snoozed: "#4a7fd5",
	done: "#3ab26b",
	dropped: "#9a8f7a",
	promoted: "#a06bd5",
};

export function statusColor(status: string): string {
	return STATUS_COLORS[status] ?? STATUS_COLORS.waiting!;
}

/** Id of the synthetic drop target "no topic" (the project itself) in the tree. */
export const NO_TOPIC = "";

/** The item statuses an event trigger can wait for. */
export const EVENT_STATUSES = ["In progress", "Awaiting confirmation", "Completed", "Rejected"] as const;
