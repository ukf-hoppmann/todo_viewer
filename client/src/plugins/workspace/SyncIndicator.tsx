import AutorenewIcon from "@mui/icons-material/Autorenew";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { Box, IconButton, Tooltip } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useGetSyncStatusQuery, type Project } from "./api";
import { needsAttention, syncView } from "./sync";
import { SyncDialog } from "./SyncDialog";
import { workspaceTestIds } from "./testIds";

/** The class of the ↻ sign; the project row shows it only while it is hovered or focused. */
export const SYNC_AUTO_CLASS = "workspace-sync-auto";

/**
 * ⚠ if the mirror of the project needs the owner (a button that opens the sync of the project), ↻ if it syncs by
 * itself; nothing for a project without mirror.
 */
export function SyncIndicator({ project }: { project: Project }) {
	const { t } = useTranslation("workspace");
	const { data: status } = useGetSyncStatusQuery(project.uid, { skip: !project.mirror_enabled });
	const [syncing, setSyncing] = useState(false);
	const view = syncView(project, status);
	const attention = needsAttention(view);
	const hint =
		view.kind === "paused"
			? t("sync.paused", { reason: t(`sync.reasons.${view.reason ?? "unknown"}`, { defaultValue: view.reason ?? "" }) })
			: t("sync.needsYou");

	return (
		<Box sx={{ display: "flex", alignItems: "center", gap: 0.25 }}>
			{attention && (
				<Tooltip title={hint}>
					<IconButton size="small" aria-label={hint} onClick={() => setSyncing(true)} data-testid={workspaceTestIds.syncAttention(project.uid)}>
						<WarningAmberIcon fontSize="small" color="warning" />
					</IconButton>
				</Tooltip>
			)}
			{project.mirror_enabled && project.auto_sync && (
				<Tooltip title={t("sync.auto")}>
					<AutorenewIcon
						fontSize="small"
						color="action"
						className={SYNC_AUTO_CLASS}
						data-testid={workspaceTestIds.syncAuto(project.uid)}
						aria-label={t("sync.auto")}
					/>
				</Tooltip>
			)}
			{syncing && <SyncDialog project={project} onClose={() => setSyncing(false)} />}
		</Box>
	);
}
