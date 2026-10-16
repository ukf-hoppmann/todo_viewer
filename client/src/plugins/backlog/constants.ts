export const STATUSES = ["Open", "In progress", "Awaiting confirmation", "Completed", "Rejected"] as const;
export const PRIORITIES = ["Urgent", "Important", "Normal", "Prospective"] as const;
/** Hidden by default: the finished items (they still count for the progress). */
export const DEFAULT_HIDDEN_STATUSES: readonly string[] = ["Completed", "Rejected"];

export const STATUS_COLORS: Record<string, string> = {
	Open: "#6b7280",
	"In progress": "#d59a3a",
	"Awaiting confirmation": "#a06bd5",
	Completed: "#3ab26b",
	Rejected: "#d5544a",
};

export const PRIORITY_COLORS: Record<string, string> = {
	Urgent: "#e05a4e",
	Important: "#d5a13a",
	Normal: "#6b7280",
	Prospective: "#4a7fd5",
};

export function statusColor(status: string): string {
	return STATUS_COLORS[status] ?? STATUS_COLORS.Open!;
}

export function priorityColor(priority: string): string {
	return PRIORITY_COLORS[priority] ?? PRIORITY_COLORS.Normal!;
}
