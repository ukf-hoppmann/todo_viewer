import type { ComponentType } from "react";

type Icon = ComponentType<{ fontSize?: "small" | "medium" | "inherit" }>;

/** An action of an entry in the list of due things: an icon with its label, or a small text button without icon. */
export interface AttentionAction {
	id: string;
	/** Translated by the contributing plugin. */
	label: string;
	icon?: Icon;
	run(): void;
	testId: string;
}

/**
 * Something due that wants the owner's attention now (a fired alarm, a due note), as a plugin reports it through
 * `useReportAttention`. The texts are translated by the contributing plugin.
 */
export interface AttentionEntry {
	/** Unique over all plugins: `<owner id>:<uid>`. */
	key: string;
	projectUid: string;
	/** Since when it is due (ISO, UTC); the newest comes first. */
	dueSince: string;
	/** The kind (alarm, note …). */
	icon: Icon;
	title: string;
	/** Shown when the entry is unfolded, e.g. the elements of an alarm or the reason and topic of a note. */
	caption?: string;
	actions: AttentionAction[];
	/** Shows the element; the list closes afterwards. */
	open(): void;
}

/** The newest first (by `dueSince`), then by key, so the order is stable. */
export function sortAttention(entries: readonly AttentionEntry[]): AttentionEntry[] {
	return [...entries].sort((a, b) => b.dueSince.localeCompare(a.dueSince) || a.key.localeCompare(b.key));
}

/** The entries of one project, or all of them without a project. */
export function attentionFor(entries: readonly AttentionEntry[], projectUid?: string): AttentionEntry[] {
	return projectUid === undefined ? [...entries] : entries.filter((entry) => entry.projectUid === projectUid);
}

/** A point in time in short: only the clock for today, otherwise weekday, date and clock (local time). */
export function formatDueSince(iso: string, language: string, now: Date = new Date()): string {
	const date = new Date(iso);
	if (date.toDateString() === now.toDateString()) return date.toLocaleTimeString(language, { hour: "2-digit", minute: "2-digit" });
	return date.toLocaleString(language, { weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}
