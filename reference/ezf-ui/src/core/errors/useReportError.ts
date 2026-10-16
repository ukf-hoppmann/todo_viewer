import { useContext } from "react";
import { LoggerOriginContext } from "../logging/LoggerOriginContext";
import { errors } from "./errors";
import type { ReportError } from "./types";

/** `reportError` for the origin of the nearest `LoggerOriginProvider`, otherwise `core`. */
export function useReportError(): ReportError {
	return errors.forOrigin(useContext(LoggerOriginContext));
}
