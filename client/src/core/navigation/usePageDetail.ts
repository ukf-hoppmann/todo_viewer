import { useContext, useEffect, type ReactNode } from "react";
import { useLogger } from "../logging/useLogger";
import { PageDetailContext } from "./PageDetailContext";

/**
 * Lets the page that is shown fill the detail column at the right of its main route, for example with the
 * detail of the selected element; `undefined`, `null`, `false` or `""` hide the column. The content applies while the page
 * is shown and disappears with it. The column itself (width, scrolling, divider) belongs to the layout; a close
 * button belongs to the content (`DetailPanel`). If the main route did not ask for a detail column
 * (`layout.detail`), nothing is shown and, in development, a warning is logged.
 */
export function usePageDetail(content: ReactNode): void {
	const detail = useContext(PageDetailContext);
	const logger = useLogger();
	const enabled = detail?.enabled;
	const set = detail?.set;

	useEffect(() => {
		if (enabled !== false || !import.meta.env.DEV) return;
		logger.warn({
			action: "page-detail",
			message: "usePageDetail was called, but the main route has no detail column (`layout.detail` is not set)",
		});
	}, [enabled, logger]);

	useEffect(() => {
		if (!enabled || !set) return;
		// `selected && <Detail />` gives `null`, `false` or `""` for "nothing selected": all of them hide the column.
		set(content === null || content === false || content === "" ? undefined : content);
		return () => set(undefined);
	}, [enabled, set, content]);
}
