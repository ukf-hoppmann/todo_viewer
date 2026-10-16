import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { usePageHeader } from "../../../core";

/** The page of the entry `panel`: fills the header of the main route of its host and shows a text. */
export default function PanelPage() {
	const { t } = useTranslation("example-addon");
	usePageHeader(
		<Typography variant="h5" component="h2" sx={{ p: 2 }}>
			{t("panel.header")}
		</Typography>,
	);

	return (
		<Box sx={{ p: 2 }}>
			<Typography>{t("panel.text")}</Typography>
		</Box>
	);
}
