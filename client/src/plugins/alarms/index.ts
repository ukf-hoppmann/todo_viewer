import AlarmIcon from "@mui/icons-material/Alarm";
import { definePlugin } from "../../core";
import { AlarmCounter } from "./AlarmCounter";
import { AlarmSettings } from "./AlarmSettings";
import { alarmsApi } from "./api";
import { onAlarmsDue } from "./announce";
import { CreateAlarm } from "./CreateForms";
import de from "./locales/de.json";
import en from "./locales/en.json";
import { SetAlarm } from "./SetAlarm";

/**
 * Alarms: reminders at a fixed time, free with a text or reminding of elements (they expire once none of them is open
 * and go a day after they were finished or expired). The server fires them (`alarms.due`) while the viewer runs;
 * the UI shows a banner, the counter in the app bar and, if allowed, a browser notification. "Set an alarm" hangs in
 * the detail panel of every element (slot `workspace.detail-sections`), "Alarm" in the "＋ New" dialog, the main route
 * `alarms/main` lists all alarms.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	api: alarmsApi,
	eventHandlers: {
		"alarms.due": onAlarmsDue,
		"alarms.alarm.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Alarms"]));
		},
		"workspace.element.changed": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Alarms"]));
		},
		"core.reconnected": (_payload, { dispatch, api }) => {
			if (api?.util) dispatch(api.util.invalidateTags(["Alarms"]));
		},
	},
	contributions: [
		{ slot: "core.main", name: "main", title: "tab.alarms", icon: AlarmIcon, page: () => import("./pages/AlarmsPage"), layout: { sidebar: true, detail: true } },
		{ slot: "workspace.create-types", name: "alarm", component: CreateAlarm, order: 30 },
		{ slot: "workspace.detail-sections", name: "set-alarm", component: SetAlarm, order: 0 },
		{ slot: "layout-header-sidebar.header-actions", name: "counter", component: AlarmCounter, order: 1 },
		{ slot: "core.settings-sections", name: "settings", component: AlarmSettings, order: 20 },
	],
});

export { alarmsTestIds } from "./testIds";
