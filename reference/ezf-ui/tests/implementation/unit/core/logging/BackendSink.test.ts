import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BackendSink, type BackendSinkOptions } from "../../../../../src/core/logging/BackendSink";
import { createLogging } from "../../../../../src/core/logging/createLogging";
import { MemorySink } from "../../../../../src/core/logging/MemorySink";
import { toLoggable } from "../../../../../src/core/logging/toLoggable";
import type { LogEntry, SinkContext } from "../../../../../src/core/logging/types";

const URL = "/api/persistLogFromUi";

const entry: LogEntry = {
	id: "a3f9c2d1",
	time: "2026-09-30T14:32:05.123Z",
	level: "error",
	origin: "core",
	sessionId: "5c1e0b7f9a2d4e6b8c0a1f3e5d7b9c2a",
	route: "/",
	message: "boom",
};

const context: SinkContext = { level: "warn", toLoggable: (value) => toLoggable(value) };

type Answer = number | Error;

/** A fake `fetch` that answers with the given statuses (or throws the errors) in turn. */
function fakeFetch(...answers: Answer[]) {
	return vi.fn<(url: string, init: RequestInit) => Promise<Response>>(async () => {
		const answer = answers.shift() ?? 204;
		if (answer instanceof Error) throw answer;
		return new Response(answer === 204 ? null : `status ${answer}`, { status: answer });
	});
}

function setup(answers: Answer[], options: Partial<BackendSinkOptions> = {}) {
	const fetch = fakeFetch(...answers);
	const onFailure = vi.fn();
	const sink = new BackendSink({ url: URL, canSend: () => true, onFailure, fetch, ...options });
	return { sink, fetch, onFailure };
}

let warn: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
	vi.useFakeTimers();
	warn = vi.spyOn(console, "warn").mockImplementation(() => {});
});

afterEach(() => {
	vi.useRealTimers();
	vi.restoreAllMocks();
});

describe("BackendSink: request", () => {
	it("is called backend", () => {
		expect(setup([]).sink.name).toBe("backend");
	});

	it("posts the entry as JSON in the backend format with the cookie", async () => {
		const { sink, fetch } = setup([204]);

		sink.write({ ...entry, data: { a: 1 } }, context);
		await vi.runAllTimersAsync();

		expect(fetch).toHaveBeenCalledTimes(1);
		const [url, init] = fetch.mock.calls[0]!;
		expect(url).toBe(URL);
		expect(init).toMatchObject({
			method: "POST",
			credentials: "include",
			keepalive: true,
			headers: { "Content-Type": "application/json" },
		});
		expect(JSON.parse(init.body as string)).toEqual({ ...entry, data: { a: 1 } });
	});

	it("uses the limits of the logging for data", async () => {
		const { sink, fetch } = setup([204]);

		sink.write({ ...entry, data: "abcdef" }, { level: "warn", toLoggable: (value) => toLoggable(value, { stringLength: 2 }) });
		await vi.runAllTimersAsync();

		expect(JSON.parse(fetch.mock.calls[0]![1].body as string).data).toBe("ab[truncated]");
	});

	it("sends large entries without keepalive, which browsers refuse above 64 kB", async () => {
		const { sink, fetch } = setup([204, 204]);

		sink.write({ ...entry, data: "x".repeat(59_000) }, context);
		sink.write({ ...entry, data: "x".repeat(61_000) }, { level: "warn", toLoggable: (value) => value });
		await vi.runAllTimersAsync();

		expect(fetch.mock.calls.map(([, init]) => init.keepalive)).toEqual([true, false]);
	});

	it("returns before the request is answered", () => {
		const fetch = vi.fn(() => new Promise<Response>(() => {}));
		const sink = new BackendSink({ url: URL, canSend: () => true, onFailure: vi.fn(), fetch });

		expect(sink.write(entry, context)).toBeUndefined();
		expect(fetch).toHaveBeenCalledTimes(1);
	});
});

describe("BackendSink: before the login", () => {
	it("sends nothing while canSend is false", async () => {
		let loggedIn = false;
		const { sink, fetch } = setup([204], { canSend: () => loggedIn });

		sink.write(entry, context);
		loggedIn = true;
		sink.write({ ...entry, id: "bbbbbbbb" }, context);
		await vi.runAllTimersAsync();

		expect(fetch).toHaveBeenCalledTimes(1);
		expect(JSON.parse(fetch.mock.calls[0]![1].body as string).id).toBe("bbbbbbbb");
	});
});

describe("BackendSink: answers", () => {
	it.each([200, 204])("is done after %i", async (status) => {
		const { sink, fetch, onFailure } = setup([status]);

		sink.write(entry, context);
		await vi.runAllTimersAsync();

		expect(fetch).toHaveBeenCalledTimes(1);
		expect(onFailure).not.toHaveBeenCalled();
		expect(warn).not.toHaveBeenCalled();
	});

	it.each([
		["a network error", new TypeError("Failed to fetch")],
		["500", 500],
		["503", 503],
	])("tries again after 1 s and 3 s on %s, then reports unreachable", async (_name, answer) => {
		const { sink, fetch, onFailure } = setup([answer, answer, answer]);

		sink.write(entry, context);
		await vi.advanceTimersByTimeAsync(0);
		expect(fetch).toHaveBeenCalledTimes(1);
		await vi.advanceTimersByTimeAsync(999);
		expect(fetch).toHaveBeenCalledTimes(1);
		await vi.advanceTimersByTimeAsync(1);
		expect(fetch).toHaveBeenCalledTimes(2);
		await vi.advanceTimersByTimeAsync(2_999);
		expect(fetch).toHaveBeenCalledTimes(2);
		await vi.advanceTimersByTimeAsync(1);
		expect(fetch).toHaveBeenCalledTimes(3);
		await vi.runAllTimersAsync();

		expect(fetch).toHaveBeenCalledTimes(3);
		expect(onFailure).toHaveBeenCalledExactlyOnceWith("unreachable");
		expect(warn).toHaveBeenCalledOnce();
		expect(String(warn.mock.calls[0])).toContain(entry.id);
	});

	it("reports nothing when a later attempt succeeds", async () => {
		const { sink, fetch, onFailure } = setup([503, 204]);

		sink.write(entry, context);
		await vi.runAllTimersAsync();

		expect(fetch).toHaveBeenCalledTimes(2);
		expect(onFailure).not.toHaveBeenCalled();
		expect(warn).not.toHaveBeenCalled();
	});

	it.each([401, 407])("reports unauthorized on %i without trying again", async (status) => {
		const { sink, fetch, onFailure } = setup([status]);

		sink.write(entry, context);
		await vi.runAllTimersAsync();

		expect(fetch).toHaveBeenCalledTimes(1);
		expect(onFailure).toHaveBeenCalledExactlyOnceWith("unauthorized");
		expect(warn).toHaveBeenCalledOnce();
	});

	it.each([400, 413])("drops the entry on %i without trying again and without onFailure", async (status) => {
		const { sink, fetch, onFailure } = setup([status]);

		sink.write(entry, context);
		await vi.runAllTimersAsync();

		expect(fetch).toHaveBeenCalledTimes(1);
		expect(onFailure).not.toHaveBeenCalled();
		expect(String(warn.mock.calls[0])).toContain(String(status));
	});

	it("shows the answer of a 400 in the warning, so that a wrong format is visible", async () => {
		const { sink } = setup([400]);

		sink.write(entry, context);
		await vi.runAllTimersAsync();

		expect(String(warn.mock.calls[0])).toContain("status 400");
	});
});

describe("BackendSink: never throws", () => {
	it("does not throw when fetch throws synchronously", async () => {
		const fetch = vi.fn(() => {
			throw new Error("sync");
		});
		const onFailure = vi.fn();
		const sink = new BackendSink({ url: URL, canSend: () => true, onFailure, fetch });

		expect(() => sink.write(entry, context)).not.toThrow();
		await vi.runAllTimersAsync();
		expect(onFailure).toHaveBeenCalledWith("unreachable");
	});

	it("does not throw when canSend or onFailure throw", async () => {
		const throwing = () => {
			throw new Error("callback");
		};
		const first = new BackendSink({ url: URL, canSend: throwing, onFailure: vi.fn(), fetch: fakeFetch() });
		const second = new BackendSink({ url: URL, canSend: () => true, onFailure: throwing, fetch: fakeFetch(401) });

		expect(() => first.write(entry, context)).not.toThrow();
		expect(() => second.write(entry, context)).not.toThrow();
		await expect(vi.runAllTimersAsync()).resolves.not.toThrow();
	});
});

describe("BackendSink with the logging", () => {
	it("gets only entries from its level on and writes no log entries itself", async () => {
		const { sink, fetch } = setup([401, 204]);
		const logging = createLogging();
		const memory = new MemorySink();
		logging.addSink(memory, { level: "debug" });
		logging.addSink(sink, { level: "warn" });
		const logger = logging.forOrigin("core");

		logger.info("not for the backend");
		logger.warn("for the backend");
		logger.error("for the backend too");
		await vi.runAllTimersAsync();

		expect(fetch.mock.calls.map(([, init]) => JSON.parse(init.body as string).level)).toEqual(["warn", "error"]);
		expect(memory.entries).toHaveLength(3);
	});
});
