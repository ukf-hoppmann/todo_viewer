import { lazy, Suspense } from "react";

const View = lazy(() => import("./ItemElementView"));

/** Loads the detail of an item only when another plugin shows one (heavy part, scope client 2). */
export function ItemElementViewLoader() {
	return (
		<Suspense fallback={null}>
			<View />
		</Suspense>
	);
}
