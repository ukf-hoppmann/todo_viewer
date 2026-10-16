import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { usePageHeader } from "../../../core";

/** The page of the entry `first`: fills the sub header and shows a text. */
export default function FirstPage() {
	const { t } = useTranslation("layout-header-sidebar");
	usePageHeader(
		<Typography variant="h5" component="h2" sx={{ p: 2 }}>
			{t("first.header")}
		</Typography>,
	);

	return (
		<Box sx={{ p: 2 }}>
			<Typography>{t("first.text")}</Typography>
		</Box>
	);
}
