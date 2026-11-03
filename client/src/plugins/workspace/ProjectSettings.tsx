import AddLinkIcon from "@mui/icons-material/AddLink";
import EditIcon from "@mui/icons-material/Edit";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SyncIcon from "@mui/icons-material/Sync";
import SyncProblemIcon from "@mui/icons-material/SyncProblem";
import { Alert, Box, Chip, Collapse, Divider, IconButton, MenuItem, Paper, TextField, Tooltip, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { IconAction } from "../../shared";
import { errorMessage, useGetSyncStatusQuery, useListProjectsQuery, useUpdateProjectMutation, type Project } from "./api";
import { ProjectCard } from "./ProjectCard";
import { SyncDialog } from "./SyncDialog";
import { needsAttention, syncView } from "./sync";
import { workspaceTestIds } from "./testIds";

type Mode = "off" | "manual" | "auto";

function modeOf(project: Project): Mode {
	if (!project.mirror_enabled) return "off";
	return project.auto_sync ? "auto" : "manual";
}

/**
 * The section "Projects" of the settings page: one compact row per project with its state, its mirror mode and the
 * actions as icons; folder, direction and last sync are in a detail that is closed at first.
 */
export function ProjectSettings() {
	const { t } = useTranslation("workspace");
	const { data: projects = [] } = useListProjectsQuery();
	return (
		<Box data-testid={workspaceTestIds.settings} sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
			<Typography variant="h6" component="h3">
				{t("settings.title")}
			</Typography>
			<Typography variant="body2" color="text.secondary">
				{t("settings.description")}
			</Typography>
			<Paper variant="outlined">
				{projects.map((project, index) => (
					<Box key={project.uid}>
						{index > 0 && <Divider />}
						<SettingsRow project={project} />
					</Box>
				))}
			</Paper>
		</Box>
	);
}

function SettingsRow({ project }: { project: Project }) {
	const { t, i18n } = useTranslation("workspace");
	const { data: status } = useGetSyncStatusQuery(project.uid, { skip: !project.mirror_enabled });
	const [update] = useUpdateProjectMutation();
	const [expanded, setExpanded] = useState(false);
	const [editing, setEditing] = useState(false);
	const [syncing, setSyncing] = useState(false);
	const [error, setError] = useState<string>();
	const view = syncView(project, status);

	const setMode = async (mode: Mode) => {
		if (mode !== "off" && !project.mirror_folder) {
			setEditing(true); // ein Spiegel braucht einen Ordner: die Karte fragt danach
			return;
		}
		setError(undefined);
		const result = await update({ uid: project.uid, version: project.version, mirror_enabled: mode !== "off", auto_sync: mode === "auto" });
		if ("error" in result) setError(errorMessage(result.error, t("card.failed")));
	};

	const label = (() => {
		switch (view.kind) {
			case "off":
				return t("sync.notMirrored");
			case "loading":
				return "…";
			case "in_sync":
				return t("sync.inSync");
			case "needs_you":
				return t("sync.needsYou");
			case "paused":
				return t("sync.paused", { reason: t(`sync.reasons.${view.reason ?? "unknown"}`, { defaultValue: view.reason ?? "" }) });
		}
	})();

	return (
		<Box sx={{ px: 1.5, py: 0.75 }} data-testid={workspaceTestIds.settingsProject(project.uid)}>
			<Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
				<Typography variant="subtitle1" noWrap sx={{ flexGrow: 1, minWidth: 120 }}>
					{project.name}
				</Typography>
				<Chip size="small" color={needsAttention(view) ? "warning" : view.kind === "in_sync" ? "success" : "default"} label={label} data-testid={workspaceTestIds.settingsState(project.uid)} />
				<TextField
					select
					size="small"
					value={modeOf(project)}
					onChange={(event) => void setMode(event.target.value as Mode)}
					sx={{ minWidth: 170 }}
					slotProps={{ htmlInput: { "aria-label": t("settings.mode"), "data-testid": workspaceTestIds.settingsMode(project.uid) } }}
				>
					{(["off", "manual", "auto"] as const).map((mode) => (
						<MenuItem key={mode} value={mode}>
							{t(`settings.modes.${mode}`)}
						</MenuItem>
					))}
				</TextField>
				<Box sx={{ display: "flex", alignItems: "center" }}>
					<IconAction label={t("settings.edit")} icon={EditIcon} onClick={() => setEditing(true)} testId={workspaceTestIds.settingsEdit(project.uid)} />
					{project.mirror_enabled ? (
						<IconAction
							label={view.kind === "paused" ? t("settings.check") : t("settings.sync")}
							icon={view.kind === "paused" ? SyncProblemIcon : SyncIcon}
							color="primary"
							onClick={() => setSyncing(true)}
							testId={workspaceTestIds.settingsMain(project.uid)}
						/>
					) : (
						<IconAction label={t("settings.setup")} icon={AddLinkIcon} color="primary" onClick={() => setEditing(true)} testId={workspaceTestIds.settingsMain(project.uid)} />
					)}
					<Tooltip title={t("settings.details")}>
						<IconButton
							size="small"
							aria-label={t("settings.details")}
							aria-expanded={expanded}
							onClick={() => setExpanded((open) => !open)}
							data-testid={workspaceTestIds.settingsExpand(project.uid)}
						>
							<ExpandMoreIcon fontSize="small" sx={{ transform: expanded ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
						</IconButton>
					</Tooltip>
				</Box>
			</Box>
			<Collapse in={expanded} unmountOnExit>
				<Box sx={{ display: "flex", gap: 2, alignItems: "baseline", flexWrap: "wrap", pt: 0.5, pb: 0.5 }}>
					<Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1, wordBreak: "break-all" }}>
						{project.mirror_folder ? `${project.mirror_folder} · ${t(`card.directions.${project.sync_direction}`)}` : t("settings.noFolder")}
					</Typography>
					<Typography variant="caption" color="text.secondary" data-testid={workspaceTestIds.settingsLast(project.uid)}>
						{status?.last_sync ? t("settings.lastSync", { time: new Date(status.last_sync).toLocaleString(i18n.language) }) : t("settings.neverSynced")}
					</Typography>
				</Box>
			</Collapse>
			{error && <Alert severity="error">{error}</Alert>}
			{editing && <ProjectCard project={project} onClose={() => setEditing(false)} />}
			{syncing && <SyncDialog project={project} onClose={() => setSyncing(false)} />}
		</Box>
	);
}
