import { Box, Button, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { RootLayout } from "../navigation/RootLayout";
import { coreTestIds } from "../testIds";
import { useAuth } from "./useAuth";

/**
 * What a user sees without a login: the `RootLayout` without tabs and logout button (so the
 * switches for language and color scheme work), and in its main area a short sentence and the
 * button that starts the login. It has no address of its own; it takes the place of the
 * application at whatever address was opened.
 */
export function LoginPage() {
	const { t } = useTranslation("core");
	const { login } = useAuth();

	return (
		<RootLayout>
			<Box
				data-testid={coreTestIds.loginPage}
				sx={{ flexGrow: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 3, p: 2 }}
			>
				<Typography>{t("auth.title")}</Typography>
				<Button variant="contained" onClick={() => void login()} data-testid={coreTestIds.loginButton}>
					{t("auth.login")}
				</Button>
			</Box>
		</RootLayout>
	);
}
