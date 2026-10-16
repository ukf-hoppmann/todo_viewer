import { RouterProvider } from "react-router/dom";
import type { AppRouterInstance } from "./createAppRouter";

/** Renders the router of the application (see `createAppRouter`). */
export function AppRouter({ router }: { router: AppRouterInstance }) {
	return <RouterProvider router={router} />;
}
