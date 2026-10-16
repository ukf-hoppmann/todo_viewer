import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { usePageHeader } from "../../../core";

/** The page of the entry `second`: fills the sub header and shows a text. */
export default function SecondPage() {
	const { t } = useTranslation("layout-header-sidebar");
	usePageHeader(
		<Typography variant="h5" component="h2" sx={{ p: 2 }}>
			{t("second.header")}
		</Typography>,
	);

	return (
		<Box sx={{ p: 2 }}>
			<Typography>{t("second.text")}</Typography>
		</Box>
	);
}
