import { describe, expect, it, vi } from "vitest";
import { AuthCheckError } from "../../../../../src/core/auth/AuthCheckError";
import { createAuth } from "../../../../../src/core/auth/createAuth";

const url = "https://backend.et.localhost";

function setup(answer: Response | Error) {
	const fetch = vi.fn<(url: string, init: RequestInit) => Promise<Response>>(async () => {
		if (answer instanceof Error) throw answer;
		return answer;
	});
	return { fetch, auth: createAuth({ url, fetch }) };
}

async function checkFailure(check: Promise<unknown>): Promise<AuthCheckError> {
	try {
		await check;
	} catch (error) {
		if (error instanceof AuthCheckError) return error;
		throw error;
	}
	throw new Error("check did not throw");
}

describe("auth: state and check()", () => {
	it("starts as unknown, before the check", () => {
		expect(setup(new Response(null, { status: 200 })).auth.getState()).toBe("unknown");
	});

	it("asks <url>/isAuthenticated with the cookies", async () => {
		const { auth, fetch } = setup(new Response(null, { status: 200 }));

		await auth.check();

		expect(fetch).toHaveBeenCalledExactlyOnceWith(`${url}/isAuthenticated`, expect.objectContaining({ credentials: "include" }));
	});

	it("is authenticated after the answer 200", async () => {
		const { auth } = setup(new Response("true", { status: 200 }));

		await expect(auth.check()).resolves.toBe("authenticated");

		expect(auth.getState()).toBe("authenticated");
	});

	it.each([401, 407])("is unauthenticated after the answer %i", async (status) => {
		const { auth } = setup(new Response(null, { status }));

		await expect(auth.check()).resolves.toBe("unauthenticated");

		expect(auth.getState()).toBe("unauthenticated");
	});

	it("fails with the kind unreachable after a network error, keeps the cause, and stays unknown", async () => {
		const cause = new TypeError("Failed to fetch");
		const { auth } = setup(cause);

		const error = await checkFailure(auth.check());

		expect(error.kind).toBe("unreachable");
		expect(error.cause).toBe(cause);
		expect(auth.getState()).toBe("unknown");
	});

	it.each([500, 503, 404, 302])("fails with the kind unexpected after the status %i, names it, and stays unknown", async (status) => {
		const { auth } = setup(new Response(null, { status }));

		const error = await checkFailure(auth.check());

		expect(error.kind).toBe("unexpected");
		expect(error.message).toContain(String(status));
		expect(auth.getState()).toBe("unknown");
	});

	it("notifies the subscribers when the state changes", async () => {
		const { auth } = setup(new Response(null, { status: 200 }));
		const listener = vi.fn();
		auth.subscribe(listener);

		await auth.check();

		expect(listener).toHaveBeenCalledOnce();
	});

	it("does not notify a subscriber who has unsubscribed", async () => {
		const { auth } = setup(new Response(null, { status: 200 }));
		const listener = vi.fn();
		const unsubscribe = auth.subscribe(listener);
		unsubscribe();

		await auth.check();

		expect(listener).not.toHaveBeenCalled();
	});
});

describe("auth: unauthorized()", () => {
	it("turns an authenticated state into unauthenticated and notifies once", async () => {
		const { auth } = setup(new Response(null, { status: 200 }));
		await auth.check();
		const listener = vi.fn();
		auth.subscribe(listener);

		auth.unauthorized();

		expect(auth.getState()).toBe("unauthenticated");
		expect(listener).toHaveBeenCalledOnce();
	});

	it("acts like one report when it is called many times", async () => {
		const { auth } = setup(new Response(null, { status: 200 }));
		await auth.check();
		const listener = vi.fn();
		auth.subscribe(listener);

		auth.unauthorized();
		auth.unauthorized();
		auth.unauthorized();

		expect(listener).toHaveBeenCalledOnce();
	});

	it("does nothing when the state is already unauthenticated", async () => {
		const { auth } = setup(new Response(null, { status: 401 }));
		await auth.check();
		const listener = vi.fn();
		auth.subscribe(listener);

		auth.unauthorized();

		expect(listener).not.toHaveBeenCalled();
	});
});

describe("auth: check() with a time limit", () => {
	/** A backend that never answers; the request ends only when its signal is aborted. */
	function silentBackend() {
		const fetch = vi.fn<(url: string, init: RequestInit) => Promise<Response>>(
			(_url, init) =>
				new Promise((_resolve, reject) => {
					init.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
				}),
		);
		return { fetch, auth: createAuth({ url, fetch }) };
	}

	it("sends no signal without a time limit", async () => {
		const { auth, fetch } = setup(new Response(null, { status: 200 }));

		await auth.check();

		expect(fetch.mock.calls[0]![1].signal).toBeUndefined();
	});

	it("passes a signal when a time limit is given", async () => {
		const { auth, fetch } = setup(new Response(null, { status: 200 }));

		await auth.check({ timeoutMs: 5_000 });

		expect(fetch.mock.calls[0]![1].signal).toBeInstanceOf(AbortSignal);
	});

	it("fails with the kind unreachable when no answer comes within the limit", async () => {
		vi.useFakeTimers();
		try {
			const { auth } = silentBackend();
			const result = checkFailure(auth.check({ timeoutMs: 5_000 }));

			await vi.advanceTimersByTimeAsync(5_000);

			const error = await result;
			expect(error.kind).toBe("unreachable");
			expect(auth.getState()).toBe("unknown");
		} finally {
			vi.useRealTimers();
		}
	});

	it("does not abort an answer that comes in time", async () => {
		vi.useFakeTimers();
		try {
			const { auth, fetch } = setup(new Response(null, { status: 200 }));

			await expect(auth.check({ timeoutMs: 5_000 })).resolves.toBe("authenticated");
			await vi.advanceTimersByTimeAsync(10_000);

			expect((fetch.mock.calls[0]![1].signal as AbortSignal).aborted).toBe(false);
		} finally {
			vi.useRealTimers();
		}
	});
});
