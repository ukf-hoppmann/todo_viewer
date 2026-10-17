import { Box, Button, Dialog, DialogContent, DialogTitle, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useDetailElement } from "../workspace";
import { AlarmForm } from "./AlarmForm";
import { useListAlarmsQuery } from "./api";
import { alarmsTestIds } from "./testIds";

/** In the detail panel of every element: the alarms bound to it and the button "set an alarm". */
export function SetAlarm() {
	const { t, i18n } = useTranslation("alarms");
	const element = useDetailElement();
	const { data: alarms = [] } = useListAlarmsQuery({ projects: [element.projectUid] });
	const [open, setOpen] = useState(false);
	const bound = alarms.filter((alarm) => alarm.target?.uid === element.uid && alarm.status !== "Done");
	return (
		<Stack spacing={0.5} data-testid={alarmsTestIds.setAlarm}>
			<Typography variant="overline" color="text.secondary">
				{t("setAlarm.title")}
			</Typography>
			{bound.map((alarm) => (
				<Typography key={alarm.uid} variant="body2" data-testid={alarmsTestIds.elementAlarm(alarm.uid)}>
					{`${alarm.label} — ${alarm.text} · ${new Date(alarm.status === "Snoozed" && alarm.snoozed_until ? alarm.snoozed_until : alarm.at).toLocaleString(i18n.language)}`}
				</Typography>
			))}
			<Box>
				<Button size="small" variant="outlined" onClick={() => setOpen(true)} data-testid={alarmsTestIds.setAlarmButton}>
					{t("setAlarm.button")}
				</Button>
			</Box>
			{open && (
				<Dialog open onClose={() => setOpen(false)} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": alarmsTestIds.formDialog } as never }}>
					<DialogTitle>{t("setAlarm.dialogTitle", { label: element.label })}</DialogTitle>
					<DialogContent>
						<AlarmForm projectUid={element.projectUid} targetUid={element.uid} onDone={() => setOpen(false)} onCancel={() => setOpen(false)} />
					</DialogContent>
				</Dialog>
			)}
		</Stack>
	);
}
