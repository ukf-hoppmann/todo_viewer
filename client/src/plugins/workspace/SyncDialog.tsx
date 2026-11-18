import RefreshIcon from "@mui/icons-material/Refresh";
import { alpha, Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Radio, RadioGroup, FormControlLabel, TextField, Typography } from "@mui/material";
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
import { choiceBlocked, choiceEffect, decisionsOf, differences, documentContext, isDeletionConflict, isTextDiff, lineDiff, onlyWhitespaceDiffers, originKey, visibleWhitespace, withBulkChoice, type Choices, type DiffLine } from "./sync";
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
								<Button key={choice} size="small" variant="outlined" onClick={() => setPicked((current) => withBulkChoice(conflicts, current, choice, direction))} disabled={choiceBlocked(direction, choice)} data-testid={workspaceTestIds.syncAll(choice)}>
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
							<ConflictCard key={conflict.key} conflict={conflict} direction={direction} choice={picked[conflict.key]} onChoose={(choice) => setPicked((current) => ({ ...current, [conflict.key]: choice }))} />
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

function ConflictCard({ conflict, direction, choice, onChoose }: { conflict: SyncConflict; direction: SyncDirection; choice: SyncChoice | undefined; onChoose: (choice: SyncChoice) => void }) {
	const { t, i18n } = useTranslation("workspace");
	const context = documentContext(conflict);
	const rows = differences(conflict).filter((row) => !context || (row.name !== "kind" && row.name !== "item"));
	const renamed = conflict.renamed_to;
	return (
		<Box sx={{ border: 1, borderColor: "divider", borderRadius: 1, p: 1, mb: 1 }} data-testid={workspaceTestIds.syncConflict(conflict.key)}>
			<Typography variant="body2" sx={{ fontWeight: 600 }}>
				{conflict.label ?? conflict.kind} · {t(`sync.conflict.${conflict.conflict}`)}
			</Typography>
			{context && (
				<Typography variant="caption" color="text.secondary" component="div" data-testid={workspaceTestIds.syncContext(conflict.key)}>
					{t(`sync.context.${context.kind === "spec" || context.kind === "notes" ? context.kind : "other"}`, { item: context.item ?? "", kind: context.kind })}
				</Typography>
			)}
			<Typography variant="body2" sx={{ mt: 0.5 }} data-testid={workspaceTestIds.syncOrigin(conflict.key)}>
				{t(`sync.origin.${originKey(conflict)}`)}
				{conflict.synced_at && ` ${t("sync.lastSynced", { time: new Date(conflict.synced_at).toLocaleString(i18n.language) })}`}
			</Typography>
			{renamed && (
				<Alert severity="info" icon={false} sx={{ my: 0.5, py: 0 }} data-testid={workspaceTestIds.syncRename(conflict.key)}>
					{t("sync.renamedTo", { label: renamed.label ?? renamed.key, percent: Math.round(renamed.similarity * 100) })}
				</Alert>
			)}
			<Box
				component="table"
				sx={{ width: "100%", fontSize: 13, borderCollapse: "collapse", my: 0.5, "& td": { verticalAlign: "top", whiteSpace: "pre-wrap", wordBreak: "break-word", pr: 1 }, "& td:first-of-type": { whiteSpace: "nowrap" } }}
			>
				{rows.some((row) => !isTextDiff(row)) && (
					<thead>
						<tr>
							<th align="left" />
							<th align="left">{t("sync.database")}</th>
							<th align="left">{t("sync.files")}</th>
						</tr>
					</thead>
				)}
				<tbody>
					{rows.map((row) => (
						<tr key={row.name} data-testid={workspaceTestIds.syncDifference(conflict.key, row.name)}>
							<td>{row.name}</td>
							<TextCells conflictKey={conflict.key} row={row} />
						</tr>
					))}
				</tbody>
			</Box>
			<RadioGroup value={choice ?? ""} onChange={(event) => onChoose(event.target.value as SyncChoice)}>
				{choices.map((value) => (
					<FormControlLabel
						key={value}
						value={value}
						disabled={choiceBlocked(direction, value)}
						control={<Radio size="small" slotProps={{ input: { "data-testid": workspaceTestIds.syncChoice(conflict.key, value) } as never }} />}
						label={
							<Box>
								<Typography variant="body2">
									{t(`sync.choices.${value}`)}
									{conflict.recommendation === value && (
										<Chip size="small" color="primary" variant="outlined" label={t("sync.recommended")} sx={{ ml: 1 }} data-testid={workspaceTestIds.syncRecommended(conflict.key, value)} />
									)}
								</Typography>
								<Typography variant="caption" color="text.secondary">
									{choiceBlocked(direction, value) ? t("sync.blockedByDirection") : t(`sync.effect.${choiceEffect(conflict, value)}`)}
								</Typography>
								{conflict.recommendation === value && t(`sync.reason.${conflict.reason}`, { defaultValue: "" }) && (
									<Typography variant="caption" color="primary" component="div">
										{t(`sync.reason.${conflict.reason}`)}
									</Typography>
								)}
							</Box>
						}
						sx={{ alignItems: "flex-start", mb: 0.5 }}
					/>
				))}
			</RadioGroup>
		</Box>
	);
}

/** The two sides of a row; a text that exists on both sides is shown as a line diff instead of twice in full. */
function TextCells({ conflictKey, row }: { conflictKey: string; row: { name: string; database: string; files: string } }) {
	const { t } = useTranslation("workspace");
	const diff = isTextDiff(row) ? lineDiff(row.database, row.files) : null;
	if (diff) {
		return (
			<td colSpan={2}>
				<Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", alignItems: "center", mb: 0.5 }}>
					<Chip size="small" label={`− ${t("sync.diffOnlyDatabase")}`} sx={(theme) => ({ bgcolor: alpha(theme.palette.error.main, 0.25) })} />
					<Chip size="small" label={`+ ${t("sync.diffOnlyFiles")}`} sx={(theme) => ({ bgcolor: alpha(theme.palette.success.main, 0.25) })} />
				</Box>
				{onlyWhitespaceDiffers(row.database, row.files) && (
					<Alert severity="info" icon={false} sx={{ mb: 0.5, py: 0 }} data-testid={workspaceTestIds.syncWhitespaceOnly(conflictKey, row.name)}>
						{t("sync.diffWhitespaceOnly")}
					</Alert>
				)}
				<Box sx={{ maxHeight: 240, overflow: "auto", fontFamily: "monospace", fontSize: 12, border: 1, borderColor: "divider", borderRadius: 0.5 }} data-testid={workspaceTestIds.syncDiff(conflictKey, row.name)}>
					{diff.map((line, index) => (
						<DiffRow key={index} line={line} skipped={(count) => t("sync.diffSkipped", { count })} emptyLine={t("sync.diffEmptyLine")} />
					))}
				</Box>
			</td>
		);
	}
	return (
		<>
			<td>
				<Box sx={{ maxHeight: 160, overflow: "auto" }}>{row.database}</Box>
			</td>
			<td>
				<Box sx={{ maxHeight: 160, overflow: "auto" }}>{row.files}</Box>
			</td>
		</>
	);
}

/** One line of a diff: a changed line has a tinted background and a marker in its own column, an empty one is written out. */
function DiffRow({ line, skipped, emptyLine }: { line: DiffLine; skipped: (count: number) => string; emptyLine: string }) {
	if (line.op === "skip") {
		return <Box sx={{ color: "text.disabled", fontStyle: "italic", textAlign: "center", py: 0.25, bgcolor: "action.hover" }}>⋯ {skipped(line.count)} ⋯</Box>;
	}
	const changed = line.op !== "same";
	const base = line.op === "add" ? "success" : "error";
	const shown = visibleWhitespace(line.text);
	return (
		<Box
			sx={(theme) => ({
				display: "flex",
				bgcolor: changed ? alpha(theme.palette[base].main, 0.2) : undefined,
				color: changed ? "text.primary" : "text.secondary",
				fontWeight: changed ? 600 : 400,
			})}
		>
			<Box component="span" sx={(theme) => ({ width: 24, flexShrink: 0, textAlign: "center", color: changed ? theme.palette[base].main : "text.disabled", fontWeight: 700 })}>
				{line.op === "add" ? "+" : line.op === "del" ? "−" : ""}
			</Box>
			<Box component="span" sx={{ whiteSpace: "pre-wrap", wordBreak: "break-word", fontStyle: shown === null ? "italic" : undefined, opacity: shown === null ? 0.7 : 1 }}>
				{shown === null ? (changed ? `⏎ ${emptyLine}` : " ") : shown}
			</Box>
		</Box>
	);
}
