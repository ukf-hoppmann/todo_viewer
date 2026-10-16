import { fetchBaseQuery, type FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { failureKindOfStatus, type BackendFailureKind } from "../backend/classifyFailure";
import type { Connection, CreateConnectionOptions } from "./types";

/**
 * Which failure of the backend an error is, if any. A status counts also when
 * the answer was no JSON (a gateway page): RTK Query reports it as
 * `PARSING_ERROR` with the status in `originalStatus`.
 */
function failureKind(error: FetchBaseQueryError): BackendFailureKind | undefined {
	const status = error.status === "PARSING_ERROR" ? error.originalStatus : error.status;
	if (status === "FETCH_ERROR" || status === "TIMEOUT_ERROR") return failureKindOfStatus("no-response");
	if (typeof status !== "number") return undefined;
	return failureKindOfStatus(status);
}

/**
 * Creates the connection to the backend; `src/app` does this once and hands it
 * to the store, from where the base query of every API reads it. It reports
 * `unreachable` (no answer, status 500 and above) to `onFailure`; the error of the
 * request carries the same `kind`. There is no login, so no cookies are sent.
 */
export function createConnection({ url, onFailure, fetch }: CreateConnectionOptions): Connection {
	const request = fetchBaseQuery({
		baseUrl: url,
		// `fetchBaseQuery` always passes a `Request`.
		fetchFn: fetch && ((input) => fetch(input as Request)),
	});

	return {
		async baseQuery(args, api, extraOptions) {
			const result = await request(args, api, extraOptions);
			if (!result.error) return result;
			// A request that was cancelled on purpose is no failure of the backend.
			if (api.signal.aborted) return result;
			const kind = failureKind(result.error);
			if (!kind) return result;
			onFailure(kind);
			return { ...result, error: { ...result.error, kind } };
		},
	};
}
