import { Box, Button, Popover, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useFinishAlarmMutation, useListAlarmsQuery, useSnoozeAlarmMutation } from "./api";
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
								{alarm.text}
								{alarm.target && (
									<Typography variant="caption" color="text.secondary" component="span">
										{` · ${alarm.target.label}`}
									</Typography>
								)}
							</Typography>
							<Box sx={{ display: "flex", gap: 0.5 }}>
								<Button size="small" onClick={() => void finish({ uid: alarm.uid, version: alarm.version })} data-testid={alarmsTestIds.action("finish", alarm.uid)}>
									{t("action.finish")}
								</Button>
								<Button size="small" onClick={() => void snooze({ uid: alarm.uid, version: alarm.version })} data-testid={alarmsTestIds.action("snooze", alarm.uid)}>
									{t("action.snooze")}
								</Button>
							</Box>
						</Box>
					))}
				</Box>
			</Popover>
		</>
	);
}
