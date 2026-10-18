import { afterEach, describe, expect, it, vi } from "vitest";
import { BackendSink } from "../../../../../../client/src/core/logging/BackendSink";
import { createLogging } from "../../../../../../client/src/core/logging/createLogging";

function setup(fetch: (url: string, init: RequestInit) => Promise<Response>) {
	const logging = createLogging();
	logging.addSink(new BackendSink({ url: "/api/core/client-log", fetch }), { level: "warn" });
	return logging;
}

afterEach(() => vi.restoreAllMocks());

describe("BackendSink", () => {
	it("posts an entry with its ids, the session and the error in the form of the server", async () => {
		const fetch = vi.fn().mockResolvedValue(new Response('{"accepted":true}'));
		const logging = setup(fetch);

		const entry = logging.forOrigin("core").error({ action: "render", message: "errors.unexpected", error: new Error("kaputt") });

		await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
		const [url, init] = fetch.mock.calls[0] as [string, RequestInit];
		const body = JSON.parse(init.body as string);
		expect(url).toBe("/api/core/client-log");
		expect(init.method).toBe("POST");
		expect(body).toMatchObject({ id: entry.id, level: "error", origin: "core", session_id: entry.sessionId, action: "render", message: "errors.unexpected" });
		expect(body.error).toMatchObject({ name: "Error", message: "kaputt" });
	});

	it("does not send entries below the level of the sink", async () => {
		const fetch = vi.fn().mockResolvedValue(new Response("{}"));
		const logging = setup(fetch);

		logging.forOrigin("core").info("nur Info");

		await Promise.resolve();
		expect(fetch).not.toHaveBeenCalled();
	});

	it("only warns on the console when sending fails and creates no entry", async () => {
		const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
		const fetch = vi.fn().mockRejectedValue(new TypeError("offline"));
		const logging = setup(fetch);

		logging.forOrigin("core").error("boom");

		await vi.waitFor(() => expect(warn).toHaveBeenCalledTimes(1));
		expect(fetch).toHaveBeenCalledTimes(1);
	});
});
