import { useEffect } from "react";
import { useLogger } from "../logging/useLogger";
import { NavigationNotice } from "./NavigationNotice";

/** The content of a main route whose sidebar has no entry: the notice, and a warning in the log. */
export function EmptySidebar({ slot }: { slot: string }) {
	const logger = useLogger();

	useEffect(() => {
		logger.warn({ action: "navigation", message: `the sidebar '${slot}' has no entry` });
	}, [logger, slot]);

	return <NavigationNotice kind="no-entries" />;
}
