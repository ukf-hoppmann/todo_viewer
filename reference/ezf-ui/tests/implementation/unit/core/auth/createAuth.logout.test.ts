import { describe, expect, it, vi } from "vitest";
import { createAuth } from "../../../../../src/core/auth/createAuth";
import type { Errors, ReportError } from "../../../../../src/core/errors/types";
import { fakeLocation, fakeStorage } from "../../../../helpers/fakeBrowser";

const url = "https://backend.et.localhost";
const logoutAddress = "https://sso.example.org/logout?client=ezf";

type Answer = Response | Error;

function setup(answers: { logoutUrl?: Answer; logout?: Answer } = {}) {
	const calls: string[] = [];
	const fetch = vi.fn<(url: string, init: RequestInit) => Promise<Response>>(async (address) => {
		calls.push(address);
		const answer =
			address === `${url}/getLogoutUrl`
				? (answers.logoutUrl ?? new Response(JSON.stringify(logoutAddress), { status: 200 }))
				: (answers.logout ?? new Response(null, { status: 200 }));
		if (answer instanceof Error) throw answer;
		return answer;
	});
	const report = vi.fn<ReportError>(async () => {});
	const errors: Errors = { forOrigin: () => report };
	const location = fakeLocation("/patients/7");
	return { auth: createAuth({ url, fetch, errors, location, storage: fakeStorage() }), fetch, calls, report, location };
}

describe("auth: logout()", () => {
	it("asks getLogoutUrl, then getlogout, in this order, both with the cookies", async () => {
		const { auth, fetch, calls } = setup();

		await auth.logout();

		expect(calls).toEqual([`${url}/getLogoutUrl`, `${url}/getlogout`]);
		for (const [, init] of fetch.mock.calls) expect(init).toMatchObject({ credentials: "include" });
	});

	it("replaces the page by the logout address, so that nothing of the user stays in memory", async () => {
		const { auth, location } = setup();

		await auth.logout();

		expect(location.replace).toHaveBeenCalledExactlyOnceWith(logoutAddress);
		expect(location.assign).not.toHaveBeenCalled();
	});

	it("leaves only after getlogout has answered", async () => {
		const { auth, fetch, location } = setup();
		let release: (response: Response) => void = () => {};
		fetch.mockImplementation(async (address) =>
			address === `${url}/getLogoutUrl`
				? new Response(JSON.stringify(logoutAddress), { status: 200 })
				: new Promise<Response>((resolve) => {
						release = resolve;
					}),
		);

		const running = auth.logout();
		await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
		expect(location.replace).not.toHaveBeenCalled();
		release(new Response(null, { status: 200 }));
		await running;

		expect(location.replace).toHaveBeenCalledOnce();
	});

	it("does not report anything when it works", async () => {
		const { auth, report } = setup();

		await auth.logout();

		expect(report).not.toHaveBeenCalled();
	});

	it.each([
		["getLogoutUrl answers 500", { logoutUrl: new Response("x", { status: 500 }) }],
		["getLogoutUrl answers no text", { logoutUrl: new Response("7", { status: 200 }) }],
		["getLogoutUrl cannot be reached", { logoutUrl: new TypeError("Failed to fetch") }],
		["getlogout answers 500", { logout: new Response("x", { status: 500 }) }],
		["getlogout cannot be reached", { logout: new TypeError("Failed to fetch") }],
	])("reports the failure and stays on the page when %s", async (_name, answers) => {
		const { auth, report, location } = setup(answers);

		await auth.logout();

		expect(report).toHaveBeenCalledExactlyOnceWith(
			expect.objectContaining({ userMessage: { key: "auth.logoutFailed" }, action: "logout", error: expect.any(Error) }),
		);
		expect(location.replace).not.toHaveBeenCalled();
	});

	it("does not ask getlogout when getLogoutUrl failed", async () => {
		const { auth, calls } = setup({ logoutUrl: new Response("x", { status: 500 }) });

		await auth.logout();

		expect(calls).toEqual([`${url}/getLogoutUrl`]);
	});
});
