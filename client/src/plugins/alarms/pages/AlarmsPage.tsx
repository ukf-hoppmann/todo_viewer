import AddIcon from "@mui/icons-material/Add";
import { Alert, Box, Button, Chip, Dialog, DialogContent, DialogTitle, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useProjectSelection } from "../../workspace";
import { AlarmForm } from "../AlarmForm";
import { toWriteError, useFinishAlarmMutation, useListAlarmsQuery, useSnoozeAlarmMutation, type AlarmOut } from "../api";
import { sortAlarms, waitingFor } from "../model";
import { alarmsTestIds } from "../testIds";

const COLORS: Record<string, "default" | "warning" | "success" | "info"> = { Due: "warning", Pending: "default", Snoozed: "info", Done: "success" };

/** The alarms of the shown projects: fired ones first, with the actions to edit, snooze and finish; and a new one. */
export default function AlarmsPage() {
	const { t, i18n } = useTranslation("alarms");
	const { visible, marked, projects } = useProjectSelection();
	const projectUids = useMemo(() => visible.map((project) => project.uid), [visible]);
	const { data: alarms = [] } = useListAlarmsQuery({ projects: projectUids }, { skip: projectUids.length === 0 });
	const [finish] = useFinishAlarmMutation();
	const [snooze] = useSnoozeAlarmMutation();
	const [dialog, setDialog] = useState<{ alarm?: AlarmOut } | undefined>();
	const [error, setError] = useState<string>();
	const defaultProject = marked ?? projects.find((project) => project.builtin);
	const sorted = useMemo(() => sortAlarms(alarms), [alarms]);

	const run = (action: Promise<unknown>) => {
		setError(undefined);
		action.catch((failure: unknown) => setError(toWriteError(failure).message));
	};
	return (
		<Box sx={{ p: 2, maxWidth: 900 }} data-testid={alarmsTestIds.page}>
			<Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
				<Typography variant="h6" component="h2" sx={{ flexGrow: 1 }}>
					{t("page.title")}
				</Typography>
				<Button startIcon={<AddIcon />} onClick={() => setDialog({})} disabled={!defaultProject}>
					{t("page.new")}
				</Button>
			</Box>
			{error && (
				<Alert severity="error" onClose={() => setError(undefined)} sx={{ mb: 1 }}>
					{error}
				</Alert>
			)}
			{sorted.length === 0 && (
				<Typography color="text.secondary" data-testid={alarmsTestIds.empty}>
					{t("page.empty")}
				</Typography>
			)}
			{sorted.map((alarm) => (
				<Box key={alarm.uid} data-testid={alarmsTestIds.row(alarm.uid)} data-status={alarm.status} sx={{ display: "flex", alignItems: "center", gap: 1, py: 0.75, borderBottom: 1, borderColor: "divider", opacity: alarm.status === "Done" ? 0.6 : 1 }}>
					<Chip size="small" color={COLORS[alarm.status] ?? "default"} label={t(`status.${alarm.status}`)} />
					<Box sx={{ flexGrow: 1, minWidth: 0 }}>
						<Typography variant="body2" noWrap>
							{`${alarm.label} — ${alarm.text}`}
						</Typography>
						<Typography variant="caption" color="text.secondary">
							{new Date(waitingFor(alarm)).toLocaleString(i18n.language)}
							{alarm.target ? ` · ${alarm.target.label} — ${alarm.target.title}` : alarm.target_text ? ` · ${alarm.target_text}` : ""}
						</Typography>
					</Box>
					{alarm.status !== "Done" && (
						<>
							<Button size="small" onClick={() => setDialog({ alarm })} data-testid={alarmsTestIds.action("edit", alarm.uid)}>
								{t("action.edit")}
							</Button>
							<Button size="small" onClick={() => run(snooze({ uid: alarm.uid, version: alarm.version }).unwrap())} data-testid={alarmsTestIds.action("snooze", alarm.uid)}>
								{t("action.snooze")}
							</Button>
							<Button size="small" onClick={() => run(finish({ uid: alarm.uid, version: alarm.version }).unwrap())} data-testid={alarmsTestIds.action("finish", alarm.uid)}>
								{t("action.finish")}
							</Button>
						</>
					)}
				</Box>
			))}
			{dialog && defaultProject && (
				<Dialog open onClose={() => setDialog(undefined)} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": alarmsTestIds.formDialog } as never }}>
					<DialogTitle>{dialog.alarm ? t("form.editTitle", { label: dialog.alarm.label }) : t("page.new")}</DialogTitle>
					<DialogContent>
						<AlarmForm key={dialog.alarm?.version ?? "new"} projectUid={dialog.alarm?.project_uid ?? defaultProject.uid} alarm={dialog.alarm} onDone={() => setDialog(undefined)} onCancel={() => setDialog(undefined)} />
					</DialogContent>
				</Dialog>
			)}
		</Box>
	);
}
