import { Box, Button, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useAppDispatch, useAppSelector, usePageHeader, usePersistentState } from "../../../core";
import { useGetHealthQuery } from "../api";
import { exampleCountUp, selectExampleCount } from "../state/eventsSlice";
import { exampleTestIds } from "../testIds";

/**
 * The page of the tab `overview`: the status of the server from the own API (reloaded by server events), a
 * counter in the plugin's compartment of the store, and a number that survives a reload because it is kept
 * in the UI state of the server (`usePersistentState`).
 */
export default function OverviewPage() {
	const { t } = useTranslation("example");
	const dispatch = useAppDispatch();
	const count = useAppSelector(selectExampleCount);
	const { data, isError } = useGetHealthQuery();
	const [visits, setVisits] = usePersistentState("example", "visits", 0);
	usePageHeader(
		<Typography variant="h5" component="h2" sx={{ p: 2 }}>
			{t("overview.header")}
		</Typography>,
	);

	return (
		<Box sx={{ p: 2 }}>
			<Typography>{t("overview.text")}</Typography>
			<Typography sx={{ mt: 2 }}>
				{t("overview.health")}:{" "}
				<span data-testid={exampleTestIds.healthStatus}>{data?.status ?? (isError ? t("overview.failed") : t("overview.loading"))}</span>
			</Typography>
			<Typography sx={{ mt: 2 }}>
				{t("overview.counter")}: <span data-testid={exampleTestIds.counterValue}>{count}</span>
			</Typography>
			<Button variant="outlined" sx={{ mt: 1 }} data-testid={exampleTestIds.counterButton} onClick={() => dispatch(exampleCountUp())}>
				{t("overview.countUp")}
			</Button>
			<Button variant="outlined" sx={{ mt: 1, ml: 1 }} onClick={() => setVisits((previous) => previous + 1)}>
				{t("overview.visits", { count: visits })}
			</Button>
		</Box>
	);
}
