import { Alert, Box, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { coreTestIds } from "../testIds";

interface NavigationNoticeProps {
	/**
	 * `no-views`: there is no tab at all. `not-found`: the page does not exist.
	 * `unavailable`: the page belongs to a plugin that is off, failed or blocked.
	 */
	kind: "no-views" | "not-found" | "unavailable";
}

const notices = {
	"no-views": { testId: coreTestIds.noViews, textKey: "navigation.noViews" },
	"not-found": { testId: coreTestIds.notFound, textKey: "navigation.notFound" },
	unavailable: { testId: coreTestIds.unavailable, textKey: "navigation.unavailable" },
} as const;

/** The hint that takes the place of a page that cannot be shown; the tabs stay usable. */
export function NavigationNotice({ kind }: NavigationNoticeProps) {
	const { t } = useTranslation("core");

	return (
		<Box sx={{ p: 2 }}>
			<Alert
				severity="info"
				data-testid={notices[kind].testId}
				action={
					kind === "no-views" ? undefined : (
						<Button color="inherit" size="small" component={Link} to="/" data-testid={coreTestIds.homeButton}>
							{t("navigation.home")}
						</Button>
					)
				}
			>
				{t(notices[kind].textKey)}
			</Alert>
		</Box>
	);
}
