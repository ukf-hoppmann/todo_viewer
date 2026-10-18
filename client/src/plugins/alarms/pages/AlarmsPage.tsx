import AddIcon from "@mui/icons-material/Add";
import CheckIcon from "@mui/icons-material/Check";
import EditIcon from "@mui/icons-material/Edit";
import SnoozeIcon from "@mui/icons-material/Snooze";
import { Alert, Box, Button, Chip, Dialog, DialogContent, DialogTitle, IconButton, Stack, Tooltip, Typography } from "@mui/material";
import { useCallback, useMemo, useState, type ComponentType, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import { usePageDetail } from "../../../core";
import { DetailPanel, type DetailAction } from "../../../shared";
import { ElementDetail, useProjectSelection } from "../../workspace";
import { AlarmForm } from "../AlarmForm";
import { toWriteError, useFinishAlarmMutation, useListAlarmsQuery, useSnoozeAlarmMutation, type AlarmOut } from "../api";
import { sortAlarms, waitingFor } from "../model";
import { alarmsTestIds } from "../testIds";

const COLORS: Record<string, "default" | "warning" | "success" | "info"> = { Due: "warning", Pending: "default", Snoozed: "info", Done: "success" };

/** Only an alarm whose target is an element of the viewer that still exists can be opened. */
const canOpen = (alarm: AlarmOut) => alarm.target !== null && !alarm.target.deleted;

/**
 * The alarms of the shown projects: fired ones first, with the actions to edit, snooze and finish as icons; and a new
 * one. A click on a row opens the alarm with the element it refers to in the detail column, so one sees what one
 * finishes or snoozes; the element is shown by its owner through `ElementDetail` of `workspace`.
 */
export default function AlarmsPage() {
	const { t, i18n } = useTranslation("alarms");
	const { visible, marked, projects } = useProjectSelection();
	const projectUids = useMemo(() => visible.map((project) => project.uid), [visible]);
	const { data: alarms = [] } = useListAlarmsQuery({ projects: projectUids }, { skip: projectUids.length === 0 });
	const [finish] = useFinishAlarmMutation();
	const [snooze] = useSnoozeAlarmMutation();
	const [dialog, setDialog] = useState<{ alarm?: AlarmOut } | undefined>();
	const [error, setError] = useState<string>();
	const [openUid, setOpenUid] = useState<string>();
	const defaultProject = marked ?? projects.find((project) => project.builtin);
	const sorted = useMemo(() => sortAlarms(alarms), [alarms]);

	const run = (action: Promise<unknown>) => {
		setError(undefined);
		action.catch((failure: unknown) => setError(toWriteError(failure).message));
	};
	const actionsOf = (alarm: AlarmOut): DetailAction[] =>
		alarm.status === "Done"
			? []
			: [
					{ id: "edit", label: t("action.edit"), icon: EditIcon, onClick: () => setDialog({ alarm }) },
					{ id: "snooze", label: t("action.snooze"), icon: SnoozeIcon, onClick: () => run(snooze({ uid: alarm.uid, version: alarm.version }).unwrap()) },
					{ id: "finish", label: t("action.finish"), icon: CheckIcon, onClick: () => run(finish({ uid: alarm.uid, version: alarm.version }).unwrap()) },
				];
	const when = (alarm: AlarmOut) => new Date(waitingFor(alarm)).toLocaleString(i18n.language);

	const open = sorted.find((alarm) => alarm.uid === openUid && canOpen(alarm));
	const close = useCallback(() => setOpenUid(undefined), []);
	usePageDetail(
		open?.target && (
			<Box data-testid={alarmsTestIds.detail}>
				<DetailPanel
					title={`${open.label} — ${open.text}`}
					subtitle={`${t(`status.${open.status}`)} · ${when(open)}`}
					actions={actionsOf(open)}
					onClose={close}
					closeLabel={t("detail.close")}
				/>
				<ElementDetail key={open.target.uid} uid={open.target.uid} kind={open.target.kind} label={open.target.label} title={open.target.title} />
			</Box>
		),
	);

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
			{sorted.length === 0 && (
				<Typography color="text.secondary" data-testid={alarmsTestIds.empty}>
					{t("page.empty")}
				</Typography>
			)}
			{sorted.map((alarm) => {
				const openable = canOpen(alarm);
				const selected = alarm.uid === open?.uid;
				return (
					<Box
						key={alarm.uid}
						data-testid={alarmsTestIds.row(alarm.uid)}
						data-status={alarm.status}
						aria-selected={selected}
						onClick={openable ? () => setOpenUid(selected ? undefined : alarm.uid) : undefined}
						sx={{
							display: "flex",
							alignItems: "center",
							gap: 1,
							px: 1,
							py: 0.75,
							borderBottom: 1,
							borderColor: "divider",
							opacity: alarm.status === "Done" ? 0.6 : 1,
							cursor: openable ? "pointer" : undefined,
							bgcolor: selected ? "action.selected" : undefined,
							"&:hover": openable ? { bgcolor: "action.hover" } : undefined,
						}}
					>
						<Chip size="small" color={COLORS[alarm.status] ?? "default"} label={t(`status.${alarm.status}`)} />
						<Box sx={{ flexGrow: 1, minWidth: 0 }}>
							<Typography variant="body2" noWrap>
								{`${alarm.label} — ${alarm.text}`}
							</Typography>
							<Typography variant="caption" color="text.secondary" component="div" noWrap>
								{when(alarm)}
								{alarm.target ? ` · ${alarm.target.label} — ${alarm.target.title}` : alarm.target_text ? ` · ${alarm.target_text}` : ""}
							</Typography>
						</Box>
						<RowActions alarm={alarm} actions={actionsOf(alarm)} />
					</Box>
				);
			})}
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

/** The actions of a row as icon buttons with a tooltip; a click on them does not open the row. */
function RowActions({ alarm, actions }: { alarm: AlarmOut; actions: DetailAction[] }) {
	if (actions.length === 0) return null;
	const stop = (event: MouseEvent) => event.stopPropagation();
	return (
		<Stack direction="row" sx={{ flexShrink: 0 }} onClick={stop}>
			{actions.map(({ id, label, icon, onClick }) => {
				const Icon = icon as ComponentType<{ fontSize?: "small" }>;
				return (
					<Tooltip key={id} title={label}>
						<IconButton size="small" aria-label={label} onClick={onClick} data-testid={alarmsTestIds.action(id, alarm.uid)}>
							<Icon fontSize="small" />
						</IconButton>
					</Tooltip>
				);
			})}
		</Stack>
	);
}
