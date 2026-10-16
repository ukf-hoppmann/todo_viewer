import { useContext, useSyncExternalStore } from "react";
import { AuthContext } from "./AuthContext";
import type { Auth, AuthState } from "./types";

/**
 * The state of the login of the nearest `AuthProvider` (the component renders
 * again when it changes) and the two actions. Throws without a provider, so
 * that nothing is shown unprotected by mistake.
 */
export function useAuth(): { state: AuthState } & Pick<Auth, "login" | "logout"> {
	const auth = useContext(AuthContext);
	if (!auth) throw new Error("useAuth must be used inside an AuthProvider");
	const state = useSyncExternalStore(auth.subscribe, auth.getState);
	return { state, login: auth.login, logout: auth.logout };
}
