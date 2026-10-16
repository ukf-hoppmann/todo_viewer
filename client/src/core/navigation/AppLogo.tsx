import { Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

/** The name of the application in the app bar (there is no logo image); the heading of the page. */
export function AppLogo() {
	const { t } = useTranslation("core");

	return (
		<Typography component="h1" variant="h6" noWrap sx={{ mr: 4, flexShrink: 0 }}>
			{t("app.title")}
		</Typography>
	);
}
