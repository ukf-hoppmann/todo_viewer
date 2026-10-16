import { Box, Button, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useAppDispatch, useAppSelector, usePageHeader } from "../../../core";
import { useGetVersionQuery } from "../api";
import { exampleCountUp, selectExampleCount } from "../state/counterSlice";
import { exampleTestIds } from "../testIds";

/**
 * The page of the tab `overview`: fills the header of its main route, shows a
 * text, a counter from the store, and the version of the backend from the own
 * API (a hint while loading, a short text if the request fails).
 */
export default function OverviewPage() {
	const { t } = useTranslation("example");
	const count = useAppSelector(selectExampleCount);
	const dispatch = useAppDispatch();
	const { data: version, isError } = useGetVersionQuery();
	usePageHeader(
		<Typography variant="h5" component="h2" sx={{ p: 2 }}>
			{t("overview.header")}
		</Typography>,
	);

	return (
		<Box sx={{ p: 2 }}>
			<Typography>{t("overview.text")}</Typography>
			<Typography sx={{ mt: 2 }}>
				{t("overview.counter")}: <span data-testid={exampleTestIds.counterValue}>{count}</span>
			</Typography>
			<Button variant="outlined" sx={{ mt: 1 }} data-testid={exampleTestIds.counterButton} onClick={() => dispatch(exampleCountUp())}>
				{t("overview.countUp")}
			</Button>
			<Typography sx={{ mt: 2 }}>
				{t("overview.backendVersion.label")}:{" "}
				<span data-testid={exampleTestIds.backendVersion}>
					{version ?? (isError ? t("overview.backendVersion.failed") : t("overview.backendVersion.loading"))}
				</span>
			</Typography>
		</Box>
	);
}
