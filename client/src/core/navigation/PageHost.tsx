import { lazy, Suspense, useState, type ComponentType } from "react";
import { ErrorBoundary } from "../errors/ErrorBoundary";
import { LoadingIndicator } from "./LoadingIndicator";
import { clearStaleReloadGuard, loadWithStaleReload } from "./loadWithStaleReload";

interface PageHostProps {
	/** `core` or the id of the plugin the page belongs to; the origin of its log entries and errors. */
	ownerId: string;
	/** Lazy import of the page; its default export is the component. Give the host a `key` per page. */
	load: () => Promise<{ default: ComponentType }>;
}

/**
 * Loads a page when it is shown and keeps a failure to its own area: a failed
 * import or a render error replaces only the page. A lazy import that failed
 * stays failed, so "try again" creates a new one that imports again. A chunk missing after a new build
 * reloads the page once.
 */
export function PageHost({ ownerId, load }: PageHostProps) {
	const create = () =>
		lazy(async () => {
			const page = await loadWithStaleReload(load)();
			clearStaleReloadGuard();
			return page;
		});
	const [Page, setPage] = useState(create);

	return (
		<ErrorBoundary origin={ownerId} onRetry={() => setPage(create)}>
			<Suspense fallback={<LoadingIndicator />}>
				<Page />
			</Suspense>
		</ErrorBoundary>
	);
}
