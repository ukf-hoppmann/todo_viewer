import { getI18n } from "react-i18next";
import { banners, type EventContext } from "../../core";
import { alarmsApi, type AlarmOut } from "./api";
import { notificationBody } from "./model";

type Query = { unwrap(): Promise<AlarmOut[]>; unsubscribe(): void };
type Action = Parameters<EventContext["dispatch"]>[0];

/** Whether the browser may show notifications and the user allowed them. */
export function canNotify(): boolean {
	return typeof Notification !== "undefined" && Notification.permission === "granted";
}

/**
 * The server fired alarms (`alarms.due`, payload `{uids}`): reload the lists, show a banner for each (done / snooze),
 * and a browser notification if the user allowed them. The state is the server's: nothing is kept here.
 */
export function onAlarmsDue(payload: unknown, { dispatch, api }: EventContext): void {
	if (api?.util) dispatch(api.util.invalidateTags(["Alarms"]));
	const uids = new Set((payload as { uids?: string[] } | undefined)?.uids ?? []);
	if (uids.size === 0) return;
	const query = dispatch(alarmsApi.endpoints.listAlarms.initiate({ dueOnly: true }, { forceRefetch: true }) as unknown as Action) as unknown as Query;
	void query
		.unwrap()
		.then((alarms) => {
			for (const alarm of alarms.filter((entry) => uids.has(entry.uid))) announce(alarm, dispatch);
		})
		.catch(() => undefined)
		.finally(() => query.unsubscribe());
}

function announce(alarm: AlarmOut, dispatch: EventContext["dispatch"]): void {
	const act = (action: "finishAlarm" | "snoozeAlarm") => () => {
		dispatch(alarmsApi.endpoints[action].initiate({ uid: alarm.uid, version: alarm.version }) as unknown as Action);
	};
	banners.show({
		severity: "warning",
		title: { key: "alarms:banner.title" },
		message: notificationBody(alarm),
		actions: [
			{ label: { key: "alarms:action.finish" }, onClick: act("finishAlarm") },
			{ label: { key: "alarms:action.snooze" }, onClick: act("snoozeAlarm") },
		],
	});
	if (canNotify()) {
		const title = getI18n()?.t("alarms:banner.title") ?? "Alarm";
		new Notification(title, { body: notificationBody(alarm), tag: alarm.uid });
	}
}
