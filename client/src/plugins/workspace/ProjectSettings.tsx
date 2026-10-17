import { Alert, Box, Button, Chip, MenuItem, Paper, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
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

/** The section "Projects" of the settings page: one card per project with its mirror, its state and the sync. */
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
			{projects.map((project) => (
				<SettingsCard key={project.uid} project={project} />
			))}
		</Box>
	);
}

function SettingsCard({ project }: { project: Project }) {
	const { t, i18n } = useTranslation("workspace");
	const { data: status } = useGetSyncStatusQuery(project.uid, { skip: !project.mirror_enabled });
	const [update] = useUpdateProjectMutation();
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
		<Paper variant="outlined" sx={{ p: 1.5, display: "flex", flexDirection: "column", gap: 1 }} data-testid={workspaceTestIds.settingsProject(project.uid)}>
			<Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
				<Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
					{project.name}
				</Typography>
				<Chip size="small" color={needsAttention(view) ? "warning" : view.kind === "in_sync" ? "success" : "default"} label={label} data-testid={workspaceTestIds.settingsState(project.uid)} />
			</Box>
			<Box sx={{ display: "flex", gap: 2, alignItems: "center", flexWrap: "wrap" }}>
				<TextField
					select
					size="small"
					label={t("settings.mode")}
					value={modeOf(project)}
					onChange={(event) => void setMode(event.target.value as Mode)}
					sx={{ minWidth: 220 }}
					slotProps={{ htmlInput: { "data-testid": workspaceTestIds.settingsMode(project.uid) } }}
				>
					{(["off", "manual", "auto"] as const).map((mode) => (
						<MenuItem key={mode} value={mode}>
							{t(`settings.modes.${mode}`)}
						</MenuItem>
					))}
				</TextField>
				<Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1, wordBreak: "break-all" }}>
					{project.mirror_folder ? `${project.mirror_folder} · ${t(`card.directions.${project.sync_direction}`)}` : t("settings.noFolder")}
				</Typography>
				<Typography variant="caption" color="text.secondary" data-testid={workspaceTestIds.settingsLast(project.uid)}>
					{status?.last_sync ? t("settings.lastSync", { time: new Date(status.last_sync).toLocaleString(i18n.language) }) : t("settings.neverSynced")}
				</Typography>
			</Box>
			{error && <Alert severity="error">{error}</Alert>}
			<Box sx={{ display: "flex", gap: 1, justifyContent: "flex-end" }}>
				<Button size="small" onClick={() => setEditing(true)} data-testid={workspaceTestIds.settingsEdit(project.uid)}>
					{t("settings.edit")}
				</Button>
				{project.mirror_enabled ? (
					<Button size="small" variant="contained" onClick={() => setSyncing(true)} data-testid={workspaceTestIds.settingsMain(project.uid)}>
						{view.kind === "paused" ? t("settings.check") : t("settings.sync")}
					</Button>
				) : (
					<Button size="small" variant="contained" onClick={() => setEditing(true)} data-testid={workspaceTestIds.settingsMain(project.uid)}>
						{t("settings.setup")}
					</Button>
				)}
			</Box>
			{editing && <ProjectCard project={project} onClose={() => setEditing(false)} />}
			{syncing && <SyncDialog project={project} onClose={() => setSyncing(false)} />}
		</Paper>
	);
}
