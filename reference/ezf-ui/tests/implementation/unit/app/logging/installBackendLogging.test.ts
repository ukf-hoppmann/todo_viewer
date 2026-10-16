import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { installBackendLogging } from "../../../../../src/app/logging/installBackendLogging";
import { mockLogBackend } from "../../../../../src/app/logging/mockLogBackend";
import { createLogging } from "../../../../../src/core/logging/createLogging";

const apiUrl = "https://backend.et.localhost";

function setup(fetchImplementation: typeof mockLogBackend = mockLogBackend) {
	const logging = createLogging();
	const fetch = vi.fn(fetchImplementation);
	const backend = installBackendLogging({ logging, fetch });
	const connection = { loggedIn: false, onFailure: vi.fn() };
	const connect = () => backend.connect({ url: apiUrl, canSend: () => connection.loggedIn, onFailure: connection.onFailure });
	return { logging, fetch, backend, connection, connect, logger: logging.forOrigin("core") };
}

beforeEach(() => {
	vi.useFakeTimers();
});

afterEach(() => {
	vi.useRealTimers();
	vi.restoreAllMocks();
});

describe("installBackendLogging", () => {
	it("registers the output backend with the minimum level warn", () => {
		const { logging } = setup();

		expect(logging.effectiveLevel("backend", "core")).toBe("warn");
	});

	it("lets the app config override the level", () => {
		const { logging } = setup();

		logging.configure({ outputs: { backend: { level: "error" } } });

		expect(logging.effectiveLevel("backend", "core")).toBe("error");
	});

	it("sends nothing before it is connected", async () => {
		const { logger, fetch, connection } = setup();
		connection.loggedIn = true;

		logger.error("before connect");
		await vi.runAllTimersAsync();

		expect(fetch).not.toHaveBeenCalled();
	});

	it("sends nothing while the user is not logged in", async () => {
		const { logger, fetch, connect } = setup();
		connect();

		logger.error("not logged in");
		await vi.runAllTimersAsync();

		expect(fetch).not.toHaveBeenCalled();
	});

	it("sends to <api.url>/persistLogFromUi once the user is logged in, and the mock accepts the entry", async () => {
		const { logger, fetch, connect, connection } = setup();
		connect();
		connection.loggedIn = true;

		logger.error({ message: "after the login", error: new Error("boom"), data: { a: 1 } });
		await vi.runAllTimersAsync();

		expect(fetch).toHaveBeenCalledOnce();
		expect(fetch.mock.calls[0]![0]).toBe(`${apiUrl}/persistLogFromUi`);
		expect((await fetch.mock.results[0]!.value).status).toBe(204);
	});

	it("stops sending when the user is logged out again", async () => {
		const { logger, fetch, connect, connection } = setup();
		connect();
		connection.loggedIn = true;
		connection.loggedIn = false;

		logger.error("after logout");
		await vi.runAllTimersAsync();

		expect(fetch).not.toHaveBeenCalled();
	});

	it("does not send entries remembered before the login when the config releases them", async () => {
		const { logging, logger, fetch, connect, connection } = setup();

		logger.info("remembered before configure");
		logging.configure({ outputs: { backend: { level: "debug" } } });
		connect();
		connection.loggedIn = true;
		await vi.runAllTimersAsync();

		expect(fetch).not.toHaveBeenCalled();
	});

	it.each([401, 407])("reports the answer %i as unauthorized", async (status) => {
		const { logger, connect, connection } = setup(async () => new Response(null, { status }));
		connect();
		connection.loggedIn = true;

		logger.error("rejected");
		await vi.runAllTimersAsync();

		expect(connection.onFailure).toHaveBeenCalledExactlyOnceWith("unauthorized");
	});

	it("reports an unreachable backend as unreachable, once, after its own attempts", async () => {
		vi.spyOn(console, "warn").mockImplementation(() => {});
		const { logger, fetch, connect, connection } = setup(async () => Promise.reject(new TypeError("Failed to fetch")));
		connect();
		connection.loggedIn = true;

		logger.error("lost");
		await vi.runAllTimersAsync();

		expect(fetch).toHaveBeenCalledTimes(3);
		expect(connection.onFailure).toHaveBeenCalledExactlyOnceWith("unreachable");
	});

	it("reports the status 500 as unreachable", async () => {
		vi.spyOn(console, "warn").mockImplementation(() => {});
		const { logger, connect, connection } = setup(async () => new Response(null, { status: 500 }));
		connect();
		connection.loggedIn = true;

		logger.error("broken");
		await vi.runAllTimersAsync();

		expect(connection.onFailure).toHaveBeenCalledExactlyOnceWith("unreachable");
	});
});
