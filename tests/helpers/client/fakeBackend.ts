import { vi } from "vitest";
import { createConnection } from "../../../client/src/core/api/createConnection";
import type { ConnectionFetch } from "../../../client/src/core/api/types";

/** What the fake backend answers for a path: a response (read anew each time), an error to throw, or a function. */
export type FakeAnswer = Response | Error | DOMException | (() => Response | Promise<Response>);

export const fakeBackendUrl = "https://backend.et.localhost";

/**
 * A `fetch` for the connection that answers by path (`"/version"`) and keeps
 * the requests it got. A path without an answer is 404. Like the real `fetch`,
 * it refuses a request whose signal was aborted.
 */
export function fakeFetch(answers: Record<string, FakeAnswer> = {}) {
	const requests: Request[] = [];
	const fetch = vi.fn<ConnectionFetch>(async (request) => {
		requests.push(request);
		if (request.signal.aborted) throw request.signal.reason;
		const answer = answers[new URL(request.url).pathname] ?? new Response(null, { status: 404 });
		if (typeof answer === "function") return answer();
		if (answer instanceof Response) return answer.clone();
		// jsdom's `DOMException` is no `Error` of Node, so anything else is thrown as it is.
		throw answer;
	});
	return { fetch, requests };
}

/** A connection on a fake backend; `onFailure` is a spy. */
export function fakeConnection(answers: Record<string, FakeAnswer> = {}, url = fakeBackendUrl) {
	const backend = fakeFetch(answers);
	const onFailure = vi.fn<(kind: "unreachable") => void>();
	const connection = createConnection({ url, fetch: backend.fetch, onFailure });
	return { connection, onFailure, ...backend };
}
