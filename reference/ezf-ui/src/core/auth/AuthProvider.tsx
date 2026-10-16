import type { ReactNode } from "react";
import { AuthContext } from "./AuthContext";
import type { Auth } from "./types";

interface AuthProviderProps {
	auth: Auth;
	children: ReactNode;
}

/** Provides the login created by `src/app` to the components below. */
export function AuthProvider({ auth, children }: AuthProviderProps) {
	return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}
