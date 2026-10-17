import AutorenewIcon from "@mui/icons-material/Autorenew";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { Box, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useGetSyncStatusQuery, type Project } from "./api";
import { needsAttention, syncView } from "./sync";
import { workspaceTestIds } from "./testIds";

/** ⚠ if the mirror of the project needs the owner, ↻ if it syncs by itself; nothing for a project without mirror. */
export function SyncIndicator({ project }: { project: Project }) {
	const { t } = useTranslation("workspace");
	const { data: status } = useGetSyncStatusQuery(project.uid, { skip: !project.mirror_enabled });
	const view = syncView(project, status);
	const attention = needsAttention(view);

	return (
		<Box sx={{ display: "flex", alignItems: "center", gap: 0.25 }}>
			{attention && (
				<Tooltip title={view.kind === "paused" ? t("sync.paused", { reason: t(`sync.reasons.${view.reason ?? "unknown"}`, { defaultValue: view.reason ?? "" }) }) : t("sync.needsYou")}>
					<WarningAmberIcon fontSize="small" color="warning" data-testid={workspaceTestIds.syncAttention(project.uid)} aria-label={t("sync.needsYou")} />
				</Tooltip>
			)}
			{project.mirror_enabled && project.auto_sync && (
				<Tooltip title={t("sync.auto")}>
					<AutorenewIcon fontSize="small" color="action" data-testid={workspaceTestIds.syncAuto(project.uid)} aria-label={t("sync.auto")} />
				</Tooltip>
			)}
		</Box>
	);
}
