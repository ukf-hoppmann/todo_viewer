import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import SnoozeIcon from "@mui/icons-material/Snooze";
import { Box, Popover, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { IconAction } from "../../shared";
import { useFinishAlarmMutation, useListAlarmsQuery, useSnoozeAlarmMutation } from "./api";
import { heading } from "./model";
import { alarmsTestIds } from "./testIds";

/**
 * A bell with the number of fired alarms in the app bar (nothing while there are none). A click lists them with
 * "done" and "snooze"; the server tells about new ones with the event `alarms.due`.
 */
export function AlarmCounter() {
	const { t } = useTranslation("alarms");
	const { data: due = [] } = useListAlarmsQuery({ dueOnly: true });
	const [finish] = useFinishAlarmMutation();
	const [snooze] = useSnoozeAlarmMutation();
	const [anchor, setAnchor] = useState<HTMLElement | null>(null);
	if (due.length === 0) return null;
	return (
		<>
			<Box
				component="button"
				type="button"
				onClick={(event) => setAnchor(event.currentTarget)}
				aria-label={t("counter.label", { count: due.length })}
				title={t("counter.label", { count: due.length })}
				data-testid={alarmsTestIds.counter}
				sx={{ bgcolor: "transparent", border: 0, color: "warning.light", cursor: "pointer", font: "inherit", fontWeight: 700 }}
			>
				{`⏰${due.length}`}
			</Box>
			<Popover open={anchor !== null} anchorEl={anchor} onClose={() => setAnchor(null)}>
				<Box sx={{ p: 1, minWidth: 300 }} data-testid={alarmsTestIds.dueList}>
					<Typography variant="overline">{t("counter.title")}</Typography>
					{due.map((alarm) => (
						<Box key={alarm.uid} sx={{ py: 0.5 }} data-testid={alarmsTestIds.dueItem(alarm.uid)}>
							<Typography variant="body2">
								{heading(alarm)}
								{alarm.targets.length > 0 && (
									<Typography variant="caption" color="text.secondary" component="span">
										{` · ${alarm.targets.map((target) => target.label).join(", ")}`}
									</Typography>
								)}
							</Typography>
							<Box sx={{ display: "flex", gap: 0.5 }}>
								<IconAction label={t("action.finish")} icon={CheckCircleIcon} onClick={() => void finish({ uid: alarm.uid, version: alarm.version })} testId={alarmsTestIds.action("finish", alarm.uid)} />
								<IconAction label={t("action.snooze")} icon={SnoozeIcon} onClick={() => void snooze({ uid: alarm.uid, version: alarm.version })} testId={alarmsTestIds.action("snooze", alarm.uid)} />
							</Box>
						</Box>
					))}
				</Box>
			</Popover>
		</>
	);
}
