import { Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { exampleTestIds } from "./testIds";

/** A section of the settings page of the core. */
export function SettingsSection() {
	const { t } = useTranslation("example");
	return (
		<Typography data-testid={exampleTestIds.settingsText}>
			{t("settings.text")}
		</Typography>
	);
}
