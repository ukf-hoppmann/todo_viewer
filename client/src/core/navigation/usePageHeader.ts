import { useContext, useEffect, type ReactNode } from "react";
import { useLogger } from "../logging/useLogger";
import { PageHeaderContext } from "./PageHeaderContext";

/**
 * Lets the page that is shown fill the header area of its main route. The
 * content applies while the page is shown and disappears with it. A page sets
 * only its own header; nothing is passed down as props. If the main route did
 * not ask for a header (`layout.header`), nothing is shown and, in
 * development, a warning is logged.
 */
export function usePageHeader(content: ReactNode): void {
	const header = useContext(PageHeaderContext);
	const logger = useLogger();
	const enabled = header?.enabled;
	const set = header?.set;

	useEffect(() => {
		if (enabled !== false || !import.meta.env.DEV) return;
		logger.warn({
			action: "page-header",
			message: "usePageHeader was called, but the main route has no header (`layout.header` is not set)",
		});
	}, [enabled, logger]);

	useEffect(() => {
		if (!enabled || !set) return;
		set(content);
		return () => set(undefined);
	}, [enabled, set, content]);
}
