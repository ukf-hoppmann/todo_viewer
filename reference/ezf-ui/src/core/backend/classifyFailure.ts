/** How the core sees a failed request to the backend. */
export type BackendFailureKind = "unauthorized" | "unreachable";

/**
 * The one place that decides what an answer of the backend means: 401 and 407
 * both mean "not logged in", as in `src_old` (a browser reported 407 in this
 * case); no answer, a timeout, and status 500 and above mean "unreachable".
 * Any other status is for the caller.
 */
export function failureKindOfStatus(status: number | "no-response"): BackendFailureKind | undefined {
	if (status === "no-response") return "unreachable";
	if (status === 401 || status === 407) return "unauthorized";
	if (status >= 500) return "unreachable";
	return undefined;
}
