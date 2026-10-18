import AddIcon from "@mui/icons-material/Add";
import CheckIcon from "@mui/icons-material/Check";
import EditIcon from "@mui/icons-material/Edit";
import SnoozeIcon from "@mui/icons-material/Snooze";
import UndoIcon from "@mui/icons-material/Undo";
import { Alert, Box, Button, Dialog, DialogContent, DialogTitle, Typography } from "@mui/material";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { usePageDetail } from "../../../core";
import type { DetailAction } from "../../../shared";
import { useProjectSelection } from "../../workspace";
import { AlarmCard } from "../AlarmCard";
import { AlarmDetail } from "../AlarmDetail";
import { AlarmForm } from "../AlarmForm";
import { toWriteError, useFinishAlarmMutation, useListAlarmsQuery, useReopenAlarmMutation, useSnoozeAlarmMutation, type AlarmOut } from "../api";
import { groupAlarms } from "../model";
import { alarmsTestIds } from "../testIds";

/**
 * The reminders of the shown projects, grouped by time (due, today, later, finished) with the actions to edit, snooze
 * and finish as icons; a finished one can be taken back until it goes after a day. A click opens the reminder in the
 * detail column with the elements it reminds of.
 */
export default function AlarmsPage() {
	const { t } = useTranslation("alarms");
	const { visible, marked, projects } = useProjectSelection();
	const projectUids = useMemo(() => visible.map((project) => project.uid), [visible]);
	const { data: alarms = [] } = useListAlarmsQuery({ projects: projectUids }, { skip: projectUids.length === 0 });
	const [finish] = useFinishAlarmMutation();
	const [snooze] = useSnoozeAlarmMutation();
	const [reopen] = useReopenAlarmMutation();
	const [dialog, setDialog] = useState<{ alarm?: AlarmOut } | undefined>();
	const [error, setError] = useState<string>();
	const [openUid, setOpenUid] = useState<string>();
	const [expanded, setExpanded] = useState<ReadonlySet<string>>(new Set());
	const defaultProject = marked ?? projects.find((project) => project.builtin);
	const groups = useMemo(() => groupAlarms(alarms, new Date()), [alarms]);

	const toggle = (uid: string) =>
		setExpanded((current) => {
			const next = new Set(current);
			if (!next.delete(uid)) next.add(uid);
			return next;
		});
	const run = (action: Promise<unknown>) => {
		setError(undefined);
		action.catch((failure: unknown) => setError(toWriteError(failure).message));
	};
	const actionsOf = (alarm: AlarmOut): DetailAction[] => {
		const ref = { uid: alarm.uid, version: alarm.version };
		if (alarm.status === "Done") return [{ id: "reopen", label: t("action.reopen"), icon: UndoIcon, onClick: () => run(reopen(ref).unwrap()) }];
		if (alarm.status === "Expired") return [];
		return [
			{ id: "edit", label: t("action.edit"), icon: EditIcon, onClick: () => setDialog({ alarm }) },
			{ id: "snooze", label: t("action.snooze"), icon: SnoozeIcon, onClick: () => run(snooze(ref).unwrap()) },
			{ id: "finish", label: t("action.finish"), icon: CheckIcon, onClick: () => run(finish(ref).unwrap()) },
		];
	};

	const open = alarms.find((alarm) => alarm.uid === openUid);
	const close = useCallback(() => setOpenUid(undefined), []);
	usePageDetail(open && <AlarmDetail key={open.uid} alarm={open} actions={actionsOf(open)} onClose={close} />);

	return (
		<Box sx={{ p: 2 }} data-testid={alarmsTestIds.page}>
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
			{groups.length === 0 && (
				<Typography color="text.secondary" data-testid={alarmsTestIds.empty}>
					{t("page.empty")}
				</Typography>
			)}
			{groups.map((group) => (
				<Box key={group.key} data-testid={alarmsTestIds.group(group.key)} sx={{ mb: 2 }}>
					<Typography variant="overline" color={group.key === "due" ? "warning.main" : "text.secondary"} component="h3">
						{t(`group.${group.key}`)}
					</Typography>
					{group.alarms.map((alarm) => {
						const selected = alarm.uid === open?.uid;
						return (
							<AlarmCard
								key={alarm.uid}
								alarm={alarm}
								selected={selected}
								expanded={expanded.has(alarm.uid)}
								actions={actionsOf(alarm)}
								onOpen={() => setOpenUid(selected ? undefined : alarm.uid)}
								onToggle={() => toggle(alarm.uid)}
							/>
						);
					})}
				</Box>
			))}
			{dialog && defaultProject && (
				<Dialog open onClose={() => setDialog(undefined)} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": alarmsTestIds.formDialog } as never }}>
					<DialogTitle>{dialog.alarm ? t("form.editTitle") : t("page.new")}</DialogTitle>
					<DialogContent>
						<AlarmForm key={dialog.alarm?.version ?? "new"} projectUid={dialog.alarm?.project_uid ?? defaultProject.uid} alarm={dialog.alarm} onDone={() => setDialog(undefined)} onCancel={() => setDialog(undefined)} />
					</DialogContent>
				</Dialog>
			)}
		</Box>
	);
}
