import { lazy, Suspense } from "react";

const View = lazy(() => import("./MemoElementView"));

/** Loads the detail of a memo only when another plugin shows one (heavy part, scope client 2). */
export function MemoElementViewLoader() {
	return (
		<Suspense fallback={null}>
			<View />
		</Suspense>
	);
}
