import AlarmIcon from "@mui/icons-material/Alarm";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import SnoozeIcon from "@mui/icons-material/Snooze";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { viewPath } from "../../core";
import { useProjectSelection, useReportAttention, type AttentionEntry } from "../workspace";
import { useFinishAlarmMutation, useListAlarmsQuery, useSnoozeAlarmMutation } from "./api";
import { attentionOf } from "./model";
import { useOpenAlarm } from "./state";
import { alarmsTestIds } from "./testIds";

/**
 * The fired alarms for the bell of `workspace` (slot `workspace.attention-sources`), with "done" and "snooze"; opening
 * one shows it in the alarms view (its project is switched on if it was hidden).
 */
export function AlarmAttention() {
	const { t } = useTranslation("alarms");
	const { data: due } = useListAlarmsQuery({ dueOnly: true });
	const [finish] = useFinishAlarmMutation();
	const [snooze] = useSnoozeAlarmMutation();
	const [, setOpenAlarm] = useOpenAlarm();
	const { visible, toggleVisible } = useProjectSelection();
	const navigate = useNavigate();

	const entries = useMemo<AttentionEntry[]>(
		() =>
			(due ?? []).map((alarm) => {
				const ref = { uid: alarm.uid, version: alarm.version };
				return {
					...attentionOf(alarm),
					icon: AlarmIcon,
					actions: [
						{ id: "finish", label: t("action.finish"), icon: CheckCircleIcon, run: () => void finish(ref), testId: alarmsTestIds.action("finish", alarm.uid) },
						{ id: "snooze", label: t("action.snooze"), icon: SnoozeIcon, run: () => void snooze(ref), testId: alarmsTestIds.action("snooze", alarm.uid) },
					],
					open: () => {
						if (!visible.some((project) => project.uid === alarm.project_uid)) toggleVisible(alarm.project_uid);
						setOpenAlarm(alarm.uid);
						void navigate(viewPath("alarms", "main"));
					},
				};
			}),
		[due, t, finish, snooze, visible, toggleVisible, setOpenAlarm, navigate],
	);
	useReportAttention(entries);
	return null;
}
