import { Avatar, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

/** The logo in the app bar, named by the app title; shared by the frame and the login page. */
export function AppLogo() {
	const { t } = useTranslation("core");

	return (
		<Typography component="h1" sx={{ mr: 4, display: "flex" }}>
			<Avatar src="/favicon/DNA_Ball_no_BG.png" alt={t("app.title")} />
		</Typography>
	);
}
