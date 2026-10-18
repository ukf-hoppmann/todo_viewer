import type { AlarmOut } from "./api";

/** The groups of the list, in this order: what needs the user now, later today, later, and finished ones. */
export type AlarmGroupKey = "due" | "today" | "later" | "done";

export interface AlarmGroup {
	key: AlarmGroupKey;
	alarms: AlarmOut[];
}

const ORDER: readonly AlarmGroupKey[] = ["due", "today", "later", "done"];

/** Finished by hand or expired (none of its elements is open any more): it waits for nothing and goes after a day. */
export function isFinished(alarm: Pick<AlarmOut, "status">): boolean {
	return alarm.status === "Done" || alarm.status === "Expired";
}

/**
 * The alarms grouped by time: `due` (fired, or its time has passed), `today` (later today, local time), `later`, and
 * `done` (finished or expired, the last one first). Within a group by time, then by label; empty groups are left out.
 */
export function groupAlarms(alarms: readonly AlarmOut[], now: Date): AlarmGroup[] {
	const groups = new Map<AlarmGroupKey, AlarmOut[]>(ORDER.map((key) => [key, []]));
	for (const alarm of alarms) groups.get(groupOf(alarm, now))!.push(alarm);
	const byTime = (a: AlarmOut, b: AlarmOut) => waitingFor(a).localeCompare(waitingFor(b)) || a.label.localeCompare(b.label, undefined, { numeric: true });
	const byDone = (a: AlarmOut, b: AlarmOut) => (b.done_at ?? "").localeCompare(a.done_at ?? "") || byTime(a, b);
	return ORDER.map((key) => ({ key, alarms: groups.get(key)!.sort(key === "done" ? byDone : byTime) })).filter((group) => group.alarms.length > 0);
}

function groupOf(alarm: AlarmOut, now: Date): AlarmGroupKey {
	if (isFinished(alarm)) return "done";
	const when = new Date(waitingFor(alarm));
	if (alarm.status === "Due" || when <= now) return "due";
	return when.toDateString() === now.toDateString() ? "today" : "later";
}

/** What the reminder is about: its text, or the title of its first element (a reminder "of NOTE-010"). */
export function heading(alarm: Pick<AlarmOut, "text" | "targets" | "target_text">): string {
	return alarm.text || alarm.targets[0]?.title || alarm.target_text || "";
}

/** A time in short: only the clock for today, otherwise weekday, date and clock (local time). */
export function formatWhen(iso: string, language: string, now: Date = new Date()): string {
	const date = new Date(iso);
	if (date.toDateString() === now.toDateString()) return date.toLocaleTimeString(language, { hour: "2-digit", minute: "2-digit" });
	return date.toLocaleString(language, { weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

/** When the alarm speaks: its time, or the snoozed time. */
export function waitingFor(alarm: AlarmOut): string {
	return alarm.status === "Snoozed" && alarm.snoozed_until ? alarm.snoozed_until : alarm.at;
}

/** A time for `<input type="datetime-local">` in the local zone (`2026-10-20T09:00`). */
export function toInputValue(iso: string): string {
	const date = new Date(iso);
	const pad = (value: number) => String(value).padStart(2, "0");
	return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/** The ISO time (UTC) of what `<input type="datetime-local">` holds; `undefined` for an empty or invalid value. */
export function fromInputValue(value: string): string | undefined {
	if (!value) return undefined;
	const date = new Date(value);
	return Number.isNaN(date.getTime()) ? undefined : date.toISOString();
}

/** The text of the browser notification for a fired alarm: the heading with the labels of its elements. */
export function notificationBody(alarm: Pick<AlarmOut, "text" | "targets" | "target_text">): string {
	const labels = alarm.targets.map((target) => target.label).join(", ");
	return labels ? `${heading(alarm)} (${labels})` : heading(alarm);
}
