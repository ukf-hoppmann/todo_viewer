const STATUS_COLORS: Record<string, string> = {
  Open: "var(--status-open)",
  "In progress": "var(--status-progress)",
  "Awaiting confirmation": "var(--status-await)",
  Completed: "var(--status-done)",
  Rejected: "var(--status-rejected)",
};

const PRIORITY_COLORS: Record<string, string> = {
  Urgent: "var(--prio-urgent)",
  Important: "var(--prio-important)",
  Prospective: "var(--prio-later)",
};

const FALLBACK_PALETTE = ["#5b8cff", "#3ab26b", "#a06bd5", "#d59a3a", "#d5544a", "#4a7fd5"];

export function statusColor(status: string): string {
  return STATUS_COLORS[status] ?? "var(--status-open)";
}

/** Known priorities have fixed colors; unknown ones get a stable color from their name. */
export function priorityColor(priority: string | null | undefined): string {
  if (!priority) return "var(--prio-none)";
  const known = PRIORITY_COLORS[priority];
  if (known) return known;
  let hash = 0;
  for (let i = 0; i < priority.length; i++) hash = (hash * 31 + priority.charCodeAt(i)) >>> 0;
  return FALLBACK_PALETTE[hash % FALLBACK_PALETTE.length] ?? "var(--prio-none)";
}
