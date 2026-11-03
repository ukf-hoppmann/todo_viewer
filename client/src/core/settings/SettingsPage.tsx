import { Box, List, ListItemButton, ListItemText, Paper, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";
import { usePageHeader } from "../navigation/usePageHeader";
import { settingsSlot } from "../plugins/contributions";
import { useSlot } from "../plugins/useSlot";
import { coreTestIds } from "../testIds";
import { defaultSettingsGroup, groupSettingsSections, isSettingsGroup, settingsGroups } from "./settingsGroups";

/** The query parameter that names the open group: `/core/settings?group=system`. */
const groupParam = "group";

/**
 * The page of the main route `core/settings`: a navigation of the groups at the left and, at the right, one card per
 * component that plugins hang into the slot `core.settings-sections` for the open group, in the fixed order of the
 * slot. The group is in the URL (`?group=`), so a reload and a link open the same group.
 */
export default function SettingsPage() {
	const { t } = useTranslation("core");
	const sections = useSlot(settingsSlot);
	const [params] = useSearchParams();
	usePageHeader(
		<Typography variant="h5" component="h2" sx={{ p: 2 }}>
			{t("settings.title")}
		</Typography>,
	);

	const grouped = groupSettingsSections(sections);
	const requested = params.get(groupParam);
	const open = isSettingsGroup(requested) ? requested : defaultSettingsGroup(grouped);
	const visible = grouped[open];

	return (
		<Box sx={{ p: 2, display: "flex", flexDirection: { xs: "column", sm: "row" }, gap: 2, alignItems: "flex-start", maxWidth: 1200 }}>
			{sections.length === 0 ? (
				<Typography data-testid={coreTestIds.settingsEmpty}>{t("settings.empty")}</Typography>
			) : (
				<>
					<List component="nav" aria-label={t("settings.nav")} data-testid={coreTestIds.settingsNav} sx={{ width: { xs: "100%", sm: 200 }, flexShrink: 0, p: 0 }}>
						{settingsGroups.map((group) => (
							<ListItemButton
								key={group}
								component={Link}
								to={{ search: `?${groupParam}=${group}` }}
								selected={group === open}
								aria-current={group === open ? "page" : undefined}
								data-testid={coreTestIds.settingsGroup(group)}
							>
								<ListItemText primary={t(`settings.groups.${group}`)} />
							</ListItemButton>
						))}
					</List>
					<Box sx={{ display: "flex", flexDirection: "column", gap: 2, flexGrow: 1, minWidth: 0, width: "100%" }}>
						{visible.length === 0 && <Typography data-testid={coreTestIds.settingsGroupEmpty}>{t("settings.emptyGroup")}</Typography>}
						{visible.map(({ ownerId, name, component: Section }) => (
							<Paper key={`${ownerId}/${name}`} variant="outlined" sx={{ p: 2 }} data-testid={coreTestIds.settingsSection(ownerId, name)}>
								<Section />
							</Paper>
						))}
					</Box>
				</>
			)}
		</Box>
	);
}
