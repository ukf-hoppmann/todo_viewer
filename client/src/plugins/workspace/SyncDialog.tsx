import RefreshIcon from "@mui/icons-material/Refresh";
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Radio, RadioGroup, FormControlLabel, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { IconAction } from "../../shared";
import {
	errorCode,
	errorMessage,
	useExecuteSyncMutation,
	useGetSyncPreviewQuery,
	type Project,
	type SyncChoice,
	type SyncConflict,
	type SyncDirection,
	type SyncResult,
} from "./api";
import { choiceEffect, decisionsOf, differences, isDeletionConflict, withBulkChoice, type Choices } from "./sync";
import { workspaceTestIds } from "./testIds";

const directions: SyncDirection[] = ["both", "to_files", "to_database"];
const choices: SyncChoice[] = ["database", "files", "defer"];

/** The text of a failed request, with the file and the line of a format error if the server named them. */
function failureText(error: unknown, fallback: string): string {
	return errorMessage(error, fallback);
}

/**
 * The sync of one project: it loads the preview, shows the conflicts first (with the fields that differ), lets the
 * owner decide each one or all at once, and runs the sync. A decision that deletes an entry is never part of the
 * bulk buttons and needs its own choice; only then the server gets `delete_missing`.
 */
export function SyncDialog({ project, onClose }: { project: Project; onClose: () => void }) {
	const { t } = useTranslation("workspace");
	const [direction, setDirection] = useState<SyncDirection>(project.sync_direction);
	const { data: preview, error, isFetching, refetch } = useGetSyncPreviewQuery({ project: project.uid, direction }, { refetchOnMountOrArgChange: true });
	const [execute, { isLoading: running }] = useExecuteSyncMutation();
	const [picked, setPicked] = useState<Choices>({});
	const [result, setResult] = useState<SyncResult>();
	const [failure, setFailure] = useState<string>();

	const conflicts = preview?.conflicts ?? [];
	const hasDeletion = conflicts.some(isDeletionConflict);

	const run = async () => {
		if (!preview) return;
		setFailure(undefined);
		const { decisions, deleteMissing } = decisionsOf(conflicts, picked);
		const outcome = await execute({ project: project.uid, token: preview.token, direction, decisions, delete_missing: deleteMissing });
		if ("error" in outcome) {
			setFailure(failureText(outcome.error, t("sync.failed")));
			if (errorCode(outcome.error) === "sync_preview_stale") void refetch();
		} else {
			setResult(outcome.data);
			setPicked({});
			// The old preview still lists the decided conflicts and its token is used up: show what is left now.
			void refetch();
		}
	};

	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="md" slotProps={{ paper: { "data-testid": workspaceTestIds.syncDialog } as never }}>
			<DialogTitle>{t("sync.title", { name: project.name })}</DialogTitle>
			<DialogContent dividers>
				<Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 2 }}>
					<TextField
						select
						size="small"
						label={t("card.direction")}
						value={direction}
						onChange={(event) => {
							setDirection(event.target.value as SyncDirection);
							setResult(undefined);
							setPicked({});
						}}
						sx={{ minWidth: 240 }}
						slotProps={{ htmlInput: { "data-testid": workspaceTestIds.syncDirection } }}
					>
						{directions.map((value) => (
							<MenuItem key={value} value={value}>
								{t(`card.directions.${value}`)}
							</MenuItem>
						))}
					</TextField>
					<IconAction label={t("sync.reload")} icon={RefreshIcon} size="medium" onClick={() => void refetch()} disabled={isFetching} testId={workspaceTestIds.syncReload} />
					{preview && (
						<Typography variant="body2" color="text.secondary" data-testid={workspaceTestIds.syncState}>
							{t(`sync.states.${preview.state}`)}
						</Typography>
					)}
				</Box>

				{error && (
					<Alert severity="error" data-testid={workspaceTestIds.syncError}>
						{failureText(error, t("sync.failed"))}
					</Alert>
				)}
				{failure && (
					<Alert severity="error" sx={{ mb: 2 }} data-testid={workspaceTestIds.syncError}>
						{failure}
					</Alert>
				)}

				{result && (
					<Alert severity={result.conflicts_left.length > 0 ? "warning" : "success"} sx={{ mb: 2 }} data-testid={workspaceTestIds.syncResult}>
						{t("sync.result", { toDatabase: result.to_database, toFiles: result.to_files })}
						{result.created.length > 0 && ` ${t("sync.created", { labels: result.created.join(", ") })}`}
						{result.conflicts_left.length > 0 && ` ${t("sync.conflictsLeft", { count: result.conflicts_left.length })}`}
					</Alert>
				)}

				{preview && conflicts.length > 0 && (
					<Box sx={{ mb: 2 }}>
						<Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
							<Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
								{t("sync.conflicts", { count: conflicts.length })}
							</Typography>
							{(["database", "files"] as const).map((choice) => (
								<Button key={choice} size="small" variant="outlined" onClick={() => setPicked((current) => withBulkChoice(conflicts, current, choice))} data-testid={workspaceTestIds.syncAll(choice)}>
									{t(`sync.all.${choice}`)}
								</Button>
							))}
						</Box>
						{hasDeletion && (
							<Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
								{t("sync.deletionsApart")}
							</Typography>
						)}
						{conflicts.map((conflict) => (
							<ConflictCard key={conflict.key} conflict={conflict} choice={picked[conflict.key]} onChoose={(choice) => setPicked((current) => ({ ...current, [conflict.key]: choice }))} />
						))}
					</Box>
				)}

				{preview && (
					<Box data-testid={workspaceTestIds.syncTransfers}>
						<Typography variant="subtitle2">{t("sync.transfers")}</Typography>
						{preview.transfers.length === 0 ? (
							<Typography variant="body2" color="text.secondary">
								{t("sync.noTransfers")}
							</Typography>
						) : (
							preview.transfers.map((transfer) => (
								<Typography key={`${transfer.target}-${transfer.key}`} variant="body2">
									{t(`sync.targets.${transfer.target}`)} · {t(`sync.actions.${transfer.action}`)} · {transfer.label ?? transfer.kind}
								</Typography>
							))
						)}
						{preview.not_imported.length > 0 && (
							<Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
								{t("sync.notImported", { count: preview.not_imported.length })}
							</Typography>
						)}
					</Box>
				)}
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose} data-testid={workspaceTestIds.syncClose}>
					{t("sync.close")}
				</Button>
				<Button variant="contained" disabled={!preview || running || isFetching} onClick={() => void run()} data-testid={workspaceTestIds.syncExecute}>
					{t("sync.execute")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}

function ConflictCard({ conflict, choice, onChoose }: { conflict: SyncConflict; choice: SyncChoice | undefined; onChoose: (choice: SyncChoice) => void }) {
	const { t } = useTranslation("workspace");
	const rows = differences(conflict);
	return (
		<Box sx={{ border: 1, borderColor: "divider", borderRadius: 1, p: 1, mb: 1 }} data-testid={workspaceTestIds.syncConflict(conflict.key)}>
			<Typography variant="body2" sx={{ fontWeight: 600 }}>
				{conflict.label ?? conflict.kind} · {t(`sync.conflict.${conflict.conflict}`)}
			</Typography>
			<Box component="table" sx={{ width: "100%", fontSize: 13, borderCollapse: "collapse", my: 0.5 }}>
				<thead>
					<tr>
						<th align="left" />
						<th align="left">{t("sync.database")}</th>
						<th align="left">{t("sync.files")}</th>
					</tr>
				</thead>
				<tbody>
					{rows.map((row) => (
						<tr key={row.name} data-testid={workspaceTestIds.syncDifference(conflict.key, row.name)}>
							<td>{row.name}</td>
							<td>{row.database}</td>
							<td>{row.files}</td>
						</tr>
					))}
				</tbody>
			</Box>
			<RadioGroup value={choice ?? ""} onChange={(event) => onChoose(event.target.value as SyncChoice)}>
				{choices.map((value) => (
					<FormControlLabel
						key={value}
						value={value}
						control={<Radio size="small" slotProps={{ input: { "data-testid": workspaceTestIds.syncChoice(conflict.key, value) } as never }} />}
						label={
							<Box>
								<Typography variant="body2">{t(`sync.choices.${value}`)}</Typography>
								<Typography variant="caption" color="text.secondary">
									{t(`sync.effect.${choiceEffect(conflict, value)}`)}
								</Typography>
							</Box>
						}
						sx={{ alignItems: "flex-start", mb: 0.5 }}
					/>
				))}
			</RadioGroup>
		</Box>
	);
}
