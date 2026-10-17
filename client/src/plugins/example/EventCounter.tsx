import { Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useAppSelector } from "../../core";
import { selectExampleEvents } from "./state/eventsSlice";
import { exampleTestIds } from "./testIds";

/** A widget in the header: how many server events this plugin has seen. */
export function EventCounter() {
	const { t } = useTranslation("example");
	const events = useAppSelector(selectExampleEvents);
	return (
		<Typography variant="body2" data-testid={exampleTestIds.eventCounter}>
			{t("header.events", { count: events })}
		</Typography>
	);
}
