import { Box, Paper, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { usePageHeader } from "../navigation/usePageHeader";
import { useSlot } from "../plugins/useSlot";
import { coreTestIds } from "../testIds";

/**
 * The page of the main route `core/settings`: one card per component that plugins hang into the slot
 * `core.settings-sections`, in the fixed order of the slot.
 */
export default function SettingsPage() {
	const { t } = useTranslation("core");
	const sections = useSlot("core.settings-sections");
	usePageHeader(
		<Typography variant="h5" component="h2" sx={{ p: 2 }}>
			{t("settings.title")}
		</Typography>,
	);

	return (
		<Box sx={{ p: 2, display: "flex", flexDirection: "column", gap: 2, maxWidth: 960 }}>
			{sections.length === 0 && <Typography data-testid={coreTestIds.settingsEmpty}>{t("settings.empty")}</Typography>}
			{sections.map(({ ownerId, name, component: Section }) => (
				<Paper key={`${ownerId}/${name}`} variant="outlined" sx={{ p: 2 }} data-testid={coreTestIds.settingsSection(ownerId, name)}>
					<Section />
				</Paper>
			))}
		</Box>
	);
}
