import type { ReactNode } from "react";
import { LoginPage } from "./LoginPage";
import { useAuth } from "./useAuth";

/**
 * The guard around the common router node of all views: only a logged-in user
 * sees the content, a user without a login (also one whose login ended during
 * the work) sees the login page at the same address, and as long as the login
 * has not been checked nothing is shown.
 */
export function AuthGuard({ children }: { children: ReactNode }) {
	const { state } = useAuth();

	if (state === "authenticated") return children;
	if (state === "unauthenticated") return <LoginPage />;
	return null;
}
