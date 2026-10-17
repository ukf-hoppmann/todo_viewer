import type { AlarmOut } from "../../../client/src/plugins/alarms/api";

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
		target: null,
		target_text: null,
		version: 1,
		deleted: false,
		...extra,
	};
}
