import { describe, expect, it, vi } from "vitest";
import { createAuth } from "../../../../../src/core/auth/createAuth";
import { returnToKey } from "../../../../../src/core/auth/returnTo";
import type { Errors, ReportError } from "../../../../../src/core/errors/types";
import { fakeLocation, fakeStorage } from "../../../../helpers/fakeBrowser";

const url = "https://backend.et.localhost";
const keycloak = "https://sso.example.org/auth?client=ezf";

function setup({ answer = new Response(JSON.stringify(keycloak), { status: 200 }), current = "/patients/7?tab=lab#top" } = {}) {
	const fetch = vi.fn<(url: string, init: RequestInit) => Promise<Response>>(async () => answer);
	const report = vi.fn<ReportError>(async () => {});
	const errors: Errors = { forOrigin: () => report };
	const location = fakeLocation(current);
	const storage = fakeStorage();
	const now = () => 1_700_000_000_000;
	return { auth: createAuth({ url, fetch, errors, location, storage, now }), fetch, report, location, storage };
}

describe("auth: login()", () => {
	it("asks <url>/getLoginUrl with the cookies and sends the browser to the answered address", async () => {
		const { auth, fetch, location } = setup();

		await auth.login();

		expect(fetch).toHaveBeenCalledExactlyOnceWith(`${url}/getLoginUrl`, expect.objectContaining({ credentials: "include" }));
		expect(location.assign).toHaveBeenCalledExactlyOnceWith(keycloak);
		expect(location.replace).not.toHaveBeenCalled();
	});

	it("remembers path, query and fragment of the current address with the time before it leaves", async () => {
		const { auth, storage, location } = setup();
		location.assign.mockImplementation(() => {
			expect(JSON.parse(storage.getItem(returnToKey) ?? "null")).toEqual({ path: "/patients/7?tab=lab#top", savedAt: 1_700_000_000_000 });
		});

		await auth.login();

		expect(location.assign).toHaveBeenCalledOnce();
	});

	it("remembers nothing when the current address is /", async () => {
		const { auth, storage } = setup({ current: "/" });

		await auth.login();

		expect(storage.getItem(returnToKey)).toBeNull();
	});

	it("does not report anything when it works", async () => {
		const { auth, report } = setup();

		await auth.login();

		expect(report).not.toHaveBeenCalled();
	});

	it.each([
		["the backend answers 500", new Response("x", { status: 500 })],
		["the answer is no JSON", new Response("not json", { status: 200 })],
		["the answer is no text", new Response("42", { status: 200 })],
		["the answer is an empty text", new Response('""', { status: 200 })],
	])("reports the failure and stays on the page when %s", async (_name, answer) => {
		const { auth, report, location, storage } = setup({ answer });

		await auth.login();

		expect(report).toHaveBeenCalledExactlyOnceWith(
			expect.objectContaining({ userMessage: { key: "auth.loginFailed" }, action: "login", error: expect.any(Error) }),
		);
		expect(location.assign).not.toHaveBeenCalled();
		expect(storage.getItem(returnToKey)).toBeNull();
	});

	it("reports a network error with the error as cause", async () => {
		const { auth, fetch, report } = setup();
		const cause = new TypeError("Failed to fetch");
		fetch.mockRejectedValue(cause);

		await auth.login();

		expect(report).toHaveBeenCalledExactlyOnceWith(expect.objectContaining({ action: "login", error: cause }));
	});
});
