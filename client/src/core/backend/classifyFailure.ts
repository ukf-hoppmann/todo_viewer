/** How the core sees a failed request to the backend. */
export type BackendFailureKind = "unreachable";

/**
 * The one place that decides what an answer of the backend means: no answer, a
 * timeout, and status 500 and above mean "unreachable". Any other status is for
 * the caller (the server answers expected failures with a 4xx and `{code, message, details}`).
 */
export function failureKindOfStatus(status: number | "no-response"): BackendFailureKind | undefined {
	if (status === "no-response") return "unreachable";
	if (status >= 500) return "unreachable";
	return undefined;
}
