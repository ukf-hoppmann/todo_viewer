import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import RestoreIcon from "@mui/icons-material/Restore";
import { Box, Button, Checkbox, IconButton, Tooltip, Typography } from "@mui/material";
import { useCallback, useMemo, useState, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import { usePageDetail } from "../../../core";
import { ConfirmDialog } from "../../../shared";
import { errorMessage, useListTrashQuery, usePurgeElementsMutation, useRestoreElementsMutation } from "../api";
import { ElementDetail } from "../ElementDetail";
import { useProjectSelection, useSearchText } from "../state";
import { workspaceTestIds } from "../testIds";

/**
 * The trash: the deleted elements of all plugins in the projects that are shown, filtered by the search text,
 * newest first. Restore and delete for good work on one element or on the chosen ones; the server leaves out a
 * chosen element whose ancestor is chosen too. Deleting for good asks first. A click on a row shows the element in
 * the detail column (`ElementDetail`).
 */
export default function TrashPage() {
	const { t, i18n } = useTranslation("workspace");
	const { projects, visible } = useProjectSelection();
	const [search] = useSearchText();
	const { data: entries = [] } = useListTrashQuery({ projects: visible.map((project) => project.uid), query: search });
	const [restore] = useRestoreElementsMutation();
	const [purge] = usePurgeElementsMutation();
	const [chosen, setChosen] = useState<string[]>([]);
	const [asking, setAsking] = useState<string[]>();
	const [error, setError] = useState<string>();
	const projectName = useMemo(() => new Map(projects.map((project) => [project.uid, project.name])), [projects]);
	// What is chosen but no longer listed (restored elsewhere, filtered out) does not count.
	const selected = chosen.filter((uid) => entries.some((entry) => entry.uid === uid));
	const toggle = (uid: string) => setChosen((current) => (current.includes(uid) ? current.filter((entry) => entry !== uid) : [...current, uid]));
	const [shownUid, setShownUid] = useState<string>();
	const shown = entries.find((entry) => entry.uid === shownUid);
	const close = useCallback(() => setShownUid(undefined), []);
	usePageDetail(shown && <ElementDetail uid={shown.uid} kind={shown.kind} label={shown.label} title={shown.title} onClose={close} />);
	// The checkbox and the buttons of a row act on their own; a click elsewhere on the row shows the element.
	const stop = (event: MouseEvent) => event.stopPropagation();

	const act = async (action: typeof restore | typeof purge, uids: string[]) => {
		setError(undefined);
		const result = await action(uids);
		if ("error" in result) setError(errorMessage(result.error, t("trash.failed")));
		else setChosen((current) => current.filter((uid) => !uids.includes(uid)));
	};

	return (
		<Box sx={{ p: 2 }} data-testid={workspaceTestIds.trash}>
			<Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
				<Checkbox
					size="small"
					checked={entries.length > 0 && selected.length === entries.length}
					indeterminate={selected.length > 0 && selected.length < entries.length}
					disabled={entries.length === 0}
					onChange={(event) => setChosen(event.target.checked ? entries.map((entry) => entry.uid) : [])}
					slotProps={{ input: { "aria-label": t("trash.selectAll"), "data-testid": workspaceTestIds.trashSelectAll } as never }}
				/>
				<Typography variant="body2" sx={{ flexGrow: 1 }}>
					{t("trash.count", { count: entries.length })}
				</Typography>
				<Button startIcon={<RestoreIcon />} disabled={selected.length === 0} onClick={() => void act(restore, selected)} data-testid={workspaceTestIds.trashRestoreSelected}>
					{t("trash.restore")}
				</Button>
				<Button color="error" startIcon={<DeleteForeverIcon />} disabled={selected.length === 0} onClick={() => setAsking(selected)} data-testid={workspaceTestIds.trashPurgeSelected}>
					{t("trash.purge")}
				</Button>
			</Box>
			{error && (
				<Typography color="error" role="alert" data-testid={workspaceTestIds.trashError}>
					{error}
				</Typography>
			)}
			{entries.length === 0 && <Typography color="text.secondary">{t("trash.empty")}</Typography>}
			{entries.map((entry) => (
				<Box
					key={entry.uid}
					data-testid={workspaceTestIds.trashRow(entry.uid)}
					aria-selected={entry.uid === shownUid}
					onClick={() => setShownUid(entry.uid === shownUid ? undefined : entry.uid)}
					sx={{ display: "flex", alignItems: "center", gap: 1, cursor: "pointer", borderRadius: 1, bgcolor: entry.uid === shownUid ? "action.selected" : undefined, "&:hover": { bgcolor: "action.hover" } }}
				>
					<Checkbox
						size="small"
						checked={selected.includes(entry.uid)}
						onClick={stop}
						onChange={() => toggle(entry.uid)}
						slotProps={{ input: { "aria-label": t("trash.select", { label: entry.label }), "data-testid": workspaceTestIds.trashSelect(entry.uid) } as never }}
					/>
					<Typography variant="body2" sx={{ minWidth: 96, fontWeight: 600 }}>
						{entry.label}
					</Typography>
					<Typography variant="body2" sx={{ flexGrow: 1 }}>
						{entry.title}
					</Typography>
					<Typography variant="caption" color="text.secondary">
						{projectName.get(entry.project_uid)}
						{entry.deleted_at ? ` · ${new Date(entry.deleted_at).toLocaleString(i18n.language)}` : ""}
					</Typography>
					<Tooltip title={t("trash.restoreOne", { label: entry.label })}>
						<IconButton
							size="small"
							aria-label={t("trash.restoreOne", { label: entry.label })}
							onClick={(event) => {
								stop(event);
								void act(restore, [entry.uid]);
							}}
							data-testid={workspaceTestIds.trashRestore(entry.uid)}
						>
							<RestoreIcon fontSize="small" />
						</IconButton>
					</Tooltip>
					<Tooltip title={t("trash.purgeOne", { label: entry.label })}>
						<IconButton
							size="small"
							aria-label={t("trash.purgeOne", { label: entry.label })}
							onClick={(event) => {
								stop(event);
								setAsking([entry.uid]);
							}}
							data-testid={workspaceTestIds.trashPurge(entry.uid)}
						>
							<DeleteForeverIcon fontSize="small" />
						</IconButton>
					</Tooltip>
				</Box>
			))}
			<ConfirmDialog
				open={asking !== undefined}
				title={t("trash.purgeTitle")}
				message={t("trash.purgeMessage", { count: asking?.length ?? 0 })}
				confirmLabel={t("trash.purge")}
				cancelLabel={t("card.cancel")}
				onCancel={() => setAsking(undefined)}
				onConfirm={() => {
					const uids = asking ?? [];
					setAsking(undefined);
					void act(purge, uids);
				}}
			/>
		</Box>
	);
}
