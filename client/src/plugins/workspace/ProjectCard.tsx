import DeleteIcon from "@mui/icons-material/Delete";
import FolderOpenIcon from "@mui/icons-material/FolderOpen";
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, Stack, Switch, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ConfirmDialog, IconAction } from "../../shared";
import {
	errorCode,
	errorMessage,
	useCreateProjectMutation,
	useRemoveProjectMutation,
	useUpdateProjectMutation,
	type Project,
	type SyncDirection,
} from "./api";
import { FolderBrowser } from "./FolderBrowser";
import { workspaceTestIds } from "./testIds";

interface Props {
	/** The project to edit; a new one is created if missing. */
	project?: Project;
	onClose: () => void;
}

const directions: SyncDirection[] = ["both", "to_files", "to_database"];

/** The card of a project: name and mirror settings; also removes the project. */
export function ProjectCard({ project, onClose }: Props) {
	const { t } = useTranslation("workspace");
	const [name, setName] = useState(project?.name ?? "");
	const [folder, setFolder] = useState(project?.mirror_folder ?? "");
	const [mirrorEnabled, setMirrorEnabled] = useState(project?.mirror_enabled ?? false);
	const [autoSync, setAutoSync] = useState(project?.auto_sync ?? false);
	const [direction, setDirection] = useState<SyncDirection>(project?.sync_direction ?? "both");
	const [browsing, setBrowsing] = useState(false);
	const [error, setError] = useState<string>();
	const [confirmRemove, setConfirmRemove] = useState<number>();
	const [create] = useCreateProjectMutation();
	const [update] = useUpdateProjectMutation();
	const [remove] = useRemoveProjectMutation();

	const save = async () => {
		setError(undefined);
		const settings = { mirror_enabled: mirrorEnabled, auto_sync: mirrorEnabled && autoSync, sync_direction: direction };
		const result = project
			? await update({ uid: project.uid, version: project.version, name, mirror_folder: folder, ...settings })
			: await create({ name, mirror_folder: folder || null, ...settings });
		if ("error" in result) setError(errorMessage(result.error, t("card.failed")));
		else onClose();
	};

	const removeProject = async (confirm: boolean) => {
		if (!project) return;
		setError(undefined);
		const result = await remove({ uid: project.uid, version: project.version, confirm });
		if (!("error" in result)) return onClose();
		if (errorCode(result.error) === "project_not_empty") {
			const details = (result.error as { data?: { details?: { elements?: number } } }).data?.details;
			setConfirmRemove(details?.elements ?? 0);
		} else {
			setError(errorMessage(result.error, t("card.failed")));
		}
	};

	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": workspaceTestIds.projectCard } as never }}>
			<DialogTitle>{project ? t("card.edit", { name: project.name }) : t("card.create")}</DialogTitle>
			<DialogContent>
				<Stack spacing={2} sx={{ pt: 1 }}>
					<TextField
						label={t("card.name")}
						value={name}
						onChange={(event) => setName(event.target.value)}
						disabled={project?.builtin}
						autoFocus
						slotProps={{ htmlInput: { "data-testid": workspaceTestIds.cardName } }}
					/>
					<Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
						<TextField
							label={t("card.folder")}
							value={folder}
							onChange={(event) => setFolder(event.target.value)}
							fullWidth
							slotProps={{ htmlInput: { "data-testid": workspaceTestIds.cardFolder } }}
						/>
						<IconAction label={t("card.browse")} icon={FolderOpenIcon} size="medium" onClick={() => setBrowsing(true)} testId={workspaceTestIds.cardBrowse} />
					</Stack>
					<FormControlLabel
						control={<Switch checked={mirrorEnabled} onChange={(event) => setMirrorEnabled(event.target.checked)} slotProps={{ input: { "data-testid": workspaceTestIds.cardMirrorEnabled } as never }} />}
						label={t("card.mirrorEnabled")}
					/>
					<FormControlLabel
						control={<Switch checked={autoSync} disabled={!mirrorEnabled} onChange={(event) => setAutoSync(event.target.checked)} slotProps={{ input: { "data-testid": workspaceTestIds.cardAutoSync } as never }} />}
						label={t("card.autoSync")}
					/>
					<TextField
						select
						label={t("card.direction")}
						value={direction}
						onChange={(event) => setDirection(event.target.value as SyncDirection)}
						slotProps={{ htmlInput: { "data-testid": workspaceTestIds.cardDirection } }}
					>
						{directions.map((value) => (
							<MenuItem key={value} value={value}>
								{t(`card.directions.${value}`)}
							</MenuItem>
						))}
					</TextField>
					{error && (
						<Typography color="error" role="alert" data-testid={workspaceTestIds.cardError}>
							{error}
						</Typography>
					)}
				</Stack>
			</DialogContent>
			<DialogActions>
				{project && !project.builtin && (
					<Button color="error" startIcon={<DeleteIcon />} onClick={() => void removeProject(false)} sx={{ mr: "auto" }} data-testid={workspaceTestIds.cardRemove}>
						{t("card.remove")}
					</Button>
				)}
				<Button onClick={onClose} data-testid={workspaceTestIds.cardCancel}>
					{t("card.cancel")}
				</Button>
				<Button variant="contained" onClick={() => void save()} data-testid={workspaceTestIds.cardSave}>
					{t("card.save")}
				</Button>
			</DialogActions>
			{browsing && (
				<FolderBrowser
					start={folder}
					onCancel={() => setBrowsing(false)}
					onChoose={(path) => {
						setFolder(path);
						setBrowsing(false);
					}}
				/>
			)}
			<ConfirmDialog
				open={confirmRemove !== undefined}
				title={t("card.removeTitle")}
				message={t("card.removeMessage", { count: confirmRemove ?? 0 })}
				confirmLabel={t("card.remove")}
				cancelLabel={t("card.cancel")}
				onCancel={() => setConfirmRemove(undefined)}
				onConfirm={() => {
					setConfirmRemove(undefined);
					void removeProject(true);
				}}
			/>
		</Dialog>
	);
}
