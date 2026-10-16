import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { usePageHeader } from "../../../core";

/** The page of the entry `start` in the sidebar of the tab `hub`: fills the header and shows a text. */
export default function StartPage() {
	const { t } = useTranslation("example");
	usePageHeader(
		<Typography variant="h5" component="h2" sx={{ p: 2 }}>
			{t("start.header")}
		</Typography>,
	);

	return (
		<Box sx={{ p: 2 }}>
			<Typography>{t("start.text")}</Typography>
		</Box>
	);
}
