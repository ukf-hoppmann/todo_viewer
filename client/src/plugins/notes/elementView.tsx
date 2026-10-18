import { lazy, Suspense } from "react";

const View = lazy(() => import("./NoteElementView"));

/** Loads the detail of a note only when another plugin shows one (heavy part, scope client 2). */
export function NoteElementViewLoader() {
	return (
		<Suspense fallback={null}>
			<View />
		</Suspense>
	);
}
