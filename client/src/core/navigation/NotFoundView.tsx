import { useEffect } from "react";
import { useLocation } from "react-router";
import { useLogger } from "../logging/useLogger";
import { NavigationNotice } from "./NavigationNotice";
import type { ViewResolution } from "./resolveView";

interface NotFoundViewProps {
	/** Tells what the called path leads to; see `resolveView`. */
	resolve: (pathname: string) => ViewResolution;
}

/**
 * The catch-all route: shows the notice for a path without a view and
 * reports it at info level with the called path, unless the owner failed (that
 * was reported at the start).
 */
export function NotFoundView({ resolve }: NotFoundViewProps) {
	const { pathname } = useLocation();
	const logger = useLogger();
	const resolution = resolve(pathname);
	const log = resolution.kind !== "available" && resolution.log;

	useEffect(() => {
		if (!log) return;
		logger.info({ action: "navigate", message: `no view at '${pathname}'`, data: { path: pathname } });
	}, [log, logger, pathname]);

	return <NavigationNotice kind={resolution.kind === "unavailable" ? "unavailable" : "not-found"} />;
}
