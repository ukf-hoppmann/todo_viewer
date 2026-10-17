import type { AlarmOut } from "./api";

/** The statuses in the order of the list: what needs the user first. */
const ORDER: Record<string, number> = { Due: 0, Pending: 1, Snoozed: 2, Done: 3 };

/** The alarms in the order of the list: fired first, then waiting, snoozed, done; within a status by time. */
export function sortAlarms(alarms: readonly AlarmOut[]): AlarmOut[] {
	return [...alarms].sort((a, b) => (ORDER[a.status] ?? 9) - (ORDER[b.status] ?? 9) || waitingFor(a).localeCompare(waitingFor(b)) || a.label.localeCompare(b.label, undefined, { numeric: true }));
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

/** The text of the browser notification for a fired alarm. */
export function notificationBody(alarm: Pick<AlarmOut, "text" | "target">): string {
	return alarm.target ? `${alarm.text} (${alarm.target.label})` : alarm.text;
}
