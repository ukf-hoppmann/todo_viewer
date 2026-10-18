import type { AlarmOut, AlarmTarget } from "../../../client/src/plugins/alarms/api";

/** An alarm with plain defaults (project `p1`, waiting, free). */
export function alarm(uid: string, extra: Partial<AlarmOut> = {}): AlarmOut {
	return {
		uid,
		project_uid: "p1",
		label: uid.toUpperCase(),
		text: `Wecker ${uid}`,
		at: "2026-10-20T07:00:00Z",
		status: "Pending",
		snoozed_until: null,
		targets: [],
		target_text: null,
		done_at: null,
		purge_at: null,
		version: 1,
		deleted: false,
		...extra,
	};
}

/** An element an alarm reminds of (open, a story unless said otherwise). */
export function target(uid: string, extra: Partial<AlarmTarget> = {}): AlarmTarget {
	return { uid, label: uid.toUpperCase(), title: `Titel ${uid}`, kind: "story", deleted: false, open: true, ...extra };
}
