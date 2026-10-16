import { useContext } from "react";
import { LoggerContext } from "./LoggerContext";
import type { Logger } from "./types";

/** Logger of the nearest `LoggerOriginProvider`, otherwise the one for `core`. */
export function useLogger(): Logger {
	return useContext(LoggerContext);
}
