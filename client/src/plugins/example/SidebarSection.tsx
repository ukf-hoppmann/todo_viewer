import { Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { exampleTestIds } from "./testIds";

/** A section of the sidebar, shown on the main route `example/overview` only. */
export function SidebarSection() {
	const { t } = useTranslation("example");
	return (
		<Typography variant="body2" data-testid={exampleTestIds.sidebarText}>
			{t("sidebar.text")}
		</Typography>
	);
}
