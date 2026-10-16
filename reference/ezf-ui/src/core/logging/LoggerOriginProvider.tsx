import type { ReactNode } from "react";
import { LoggerContext } from "./LoggerContext";
import { LoggerOriginContext } from "./LoggerOriginContext";
import { logging } from "./logging";

interface LoggerOriginProviderProps {
	/** `core` or a plugin id. */
	origin: string;
	children: ReactNode;
}

/** Gives the components below the logger of the given origin (see `useLogger`). */
export function LoggerOriginProvider({ origin, children }: LoggerOriginProviderProps) {
	return (
		<LoggerOriginContext value={origin}>
			<LoggerContext value={logging.forOrigin(origin)}>{children}</LoggerContext>
		</LoggerOriginContext>
	);
}
