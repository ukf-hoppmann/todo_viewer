import AlarmAddIcon from "@mui/icons-material/AlarmAdd";
import { Box, Dialog, DialogContent, DialogTitle, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { IconAction } from "../../shared";
import { useDetailElement } from "../workspace";
import { AlarmForm } from "./AlarmForm";
import { useListAlarmsQuery } from "./api";
import { isFinished, waitingFor } from "./model";
import { alarmsTestIds } from "./testIds";

/** In the detail panel of every element: the reminders of it that still wait and the button "set an alarm". */
export function SetAlarm() {
	const { t, i18n } = useTranslation("alarms");
	const element = useDetailElement();
	const { data: alarms = [] } = useListAlarmsQuery({ projects: [element.projectUid] });
	const [open, setOpen] = useState(false);
	const bound = alarms.filter((alarm) => alarm.targets.some((target) => target.uid === element.uid) && !isFinished(alarm));
	return (
		<Stack spacing={0.5} data-testid={alarmsTestIds.setAlarm}>
			<Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
				<Typography variant="overline" color="text.secondary">
					{t("setAlarm.title")}
				</Typography>
				<IconAction label={t("setAlarm.button")} icon={AlarmAddIcon} onClick={() => setOpen(true)} testId={alarmsTestIds.setAlarmButton} />
			</Box>
			{bound.map((alarm) => (
				<Typography key={alarm.uid} variant="body2" data-testid={alarmsTestIds.elementAlarm(alarm.uid)}>
					{`⏰ ${new Date(waitingFor(alarm)).toLocaleString(i18n.language)}${alarm.text ? ` · ${alarm.text}` : ""}`}
				</Typography>
			))}
			{open && (
				<Dialog open onClose={() => setOpen(false)} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": alarmsTestIds.formDialog } as never }}>
					<DialogTitle>{t("setAlarm.dialogTitle", { label: element.label })}</DialogTitle>
					<DialogContent>
						<AlarmForm projectUid={element.projectUid} target={{ id: element.uid, label: element.label, title: "" }} onDone={() => setOpen(false)} onCancel={() => setOpen(false)} />
					</DialogContent>
				</Dialog>
			)}
		</Stack>
	);
}
