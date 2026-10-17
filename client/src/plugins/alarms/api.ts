import { createPluginApi } from "../../core";
import type { components } from "../../shared";

export type AlarmOut = components["schemas"]["AlarmOut"];

/** The error of a write: the code and details the server gave, as an `Error` the forms can show. */
export class WriteError extends Error {
	constructor(
		message: string,
		readonly code: string | undefined,
	) {
		super(message);
	}
}

export function toWriteError(failure: unknown): WriteError {
	if (failure instanceof WriteError) return failure;
	const data = (failure as { data?: { code?: string; message?: string } } | undefined)?.data;
	return new WriteError(data?.message ?? "Request failed", data?.code);
}

/**
 * The API of the plugin (`alarms.api`): `listAlarms` asks for the alarms of the given projects (`dueOnly`: only those
 * that have fired and wait for an answer). The tag `Alarms` is what server events invalidate.
 */
export const alarmsApi = createPluginApi(
	"alarms",
	(build) => ({
		listAlarms: build.query<AlarmOut[], { projects?: string[]; dueOnly?: boolean } | void>({
			query: (args) => ({
				url: "alarms/alarms",
				params: {
					...(args && args.projects ? { projects: args.projects.join(",") } : {}),
					...(args && args.dueOnly ? { due_only: "true" } : {}),
				},
			}),
			providesTags: ["Alarms"],
		}),
		createAlarm: build.mutation<AlarmOut, { project: string; text: string; at: string; target?: string | null }>({
			query: ({ project, ...fields }) => ({ url: "alarms/alarms", method: "POST", body: { project, fields } }),
			invalidatesTags: ["Alarms"],
		}),
		updateAlarm: build.mutation<AlarmOut, { uid: string; version: number; fields: Record<string, unknown> }>({
			query: ({ uid, ...body }) => ({ url: `alarms/alarms/${uid}`, method: "PUT", body }),
			invalidatesTags: ["Alarms"],
		}),
		snoozeAlarm: build.mutation<AlarmOut, { uid: string; version: number; until?: string }>({
			query: ({ uid, ...body }) => ({ url: `alarms/alarms/${uid}/snooze`, method: "POST", body }),
			invalidatesTags: ["Alarms"],
		}),
		finishAlarm: build.mutation<AlarmOut, { uid: string; version: number }>({
			query: ({ uid, ...body }) => ({ url: `alarms/alarms/${uid}/finish`, method: "POST", body }),
			invalidatesTags: ["Alarms"],
		}),
	}),
	{ tagTypes: ["Alarms"] },
);

export const { useListAlarmsQuery, useCreateAlarmMutation, useUpdateAlarmMutation, useSnoozeAlarmMutation, useFinishAlarmMutation } = alarmsApi;
