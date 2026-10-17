import { Box, Button, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { alarmsTestIds } from "./testIds";

type Permission = NotificationPermission | "unsupported";

function current(): Permission {
	return typeof Notification === "undefined" ? "unsupported" : Notification.permission;
}

/** The section "Alarms" of the settings page: whether the browser may show notifications when an alarm fires. */
export function AlarmSettings() {
	const { t } = useTranslation("alarms");
	const [permission, setPermission] = useState<Permission>(current);
	return (
		<Box data-testid={alarmsTestIds.settings} sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
			<Typography variant="h6" component="h3">
				{t("settings.title")}
			</Typography>
			<Typography variant="body2" color="text.secondary">
				{t("settings.description")}
			</Typography>
			<Typography variant="body2" data-testid={alarmsTestIds.permission}>
				{t(`settings.permission.${permission}`)}
			</Typography>
			{permission === "default" && (
				<Box>
					<Button
						variant="outlined"
						onClick={() => void Notification.requestPermission().then(setPermission)}
						data-testid={alarmsTestIds.enableNotifications}
					>
						{t("settings.enable")}
					</Button>
				</Box>
			)}
		</Box>
	);
}
