import { Box, CircularProgress } from "@mui/material";
import { useTranslation } from "react-i18next";
import { coreTestIds } from "../testIds";

/** The one loading indicator of the application: shown while a page is loaded. */
export function LoadingIndicator() {
	const { t } = useTranslation("core");

	return (
		<Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
			<CircularProgress aria-label={t("layout.loading")} data-testid={coreTestIds.loading} />
		</Box>
	);
}
