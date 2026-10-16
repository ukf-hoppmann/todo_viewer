import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthCheckError } from "../../../../../src/core/auth/AuthCheckError";
import type { Auth, AuthState } from "../../../../../src/core/auth/types";
import { createConnectionMonitor } from "../../../../../src/core/backend/createConnectionMonitor";
import type { ConnectionSettings } from "../../../../../src/core/backend/types";
import { createBanners } from "../../../../../src/core/banners/createBanners";

type Outcome = "ok" | "unauthenticated" | "unreachable" | "unexpected";

/** A `check` that answers with the outcomes in turn; the last one repeats. */
function scripted(...outcomes: Outcome[]) {
	let index = 0;
	return vi.fn<Auth["check"]>(async () => {
		const outcome = outcomes[Math.min(index++, outcomes.length - 1)]!;
		if (outcome === "ok") return "authenticated";
		if (outcome === "unauthenticated") return "unauthenticated";
		throw new AuthCheckError(outcome, "scripted");
	});
}

/** A `check` whose answers the test hands out by hand. */
function held() {
	const pending: Array<(state: AuthState) => void> = [];
	const check = vi.fn<Auth["check"]>(
		() =>
			new Promise<AuthState>((resolve) => {
				pending.push(resolve);
			}),
	);
	return { check, answer: (state: AuthState) => pending.shift()!(state) };
}

function setup(check: ReturnType<typeof scripted>, settings?: Partial<ConnectionSettings>) {
	const banners = createBanners();
	const unauthorized = vi.fn();
	const monitor = createConnectionMonitor({ auth: { check, unauthorized }, banners, settings });
	return { banners, unauthorized, monitor, check };
}

const visible = (banners: ReturnType<typeof createBanners>) => banners.getSnapshot().map((banner) => banner.request);
const seconds = (count: number) => vi.advanceTimersByTimeAsync(count * 1000);

beforeEach(() => {
	vi.useFakeTimers();
});

afterEach(() => {
	vi.useRealTimers();
});

describe("connection monitor: the test after a failure", () => {
	it("runs the test at once after the report, with the retry interval as time limit", async () => {
		const { monitor, check } = setup(scripted("ok"));

		monitor.report("unreachable");
		await seconds(0);

		expect(check).toHaveBeenCalledExactlyOnceWith({ timeoutMs: 5_000 });
	});

	it("takes the retry interval from the settings", async () => {
		const { monitor, check } = setup(scripted("ok"), { retryIntervalSeconds: 12 });

		monitor.report("unreachable");
		await seconds(0);

		expect(check).toHaveBeenCalledExactlyOnceWith({ timeoutMs: 12_000 });
	});

	it("never runs two tests at the same time, and does not count the reports during a test", async () => {
		const { check, answer } = held();
		const banners = createBanners();
		const monitor = createConnectionMonitor({ auth: { check, unauthorized: vi.fn() }, banners });

		monitor.report("unreachable");
		monitor.report("unreachable");
		monitor.report("unreachable");
		await seconds(30);

		expect(check).toHaveBeenCalledTimes(1);
		answer("authenticated");
	});

	it("repeats the test after the interval, counted from the end of the test", async () => {
		const { check, answer } = held();
		const monitor = createConnectionMonitor({
			auth: { check, unauthorized: vi.fn() },
			banners: createBanners(),
			settings: { retryIntervalSeconds: 5 },
		});

		monitor.report("unreachable");
		await seconds(3);
		answer("authenticated"); // The test took 3 s and worked: nothing follows.
		await seconds(60);

		expect(check).toHaveBeenCalledTimes(1);
	});

	it("starts the next test 5 s after a failed test has ended", async () => {
		const { monitor, check } = setup(scripted("unreachable", "ok"));

		monitor.report("unreachable");
		await seconds(0);
		expect(check).toHaveBeenCalledTimes(1);

		await seconds(4.9);
		expect(check).toHaveBeenCalledTimes(1);
		await seconds(0.2);
		expect(check).toHaveBeenCalledTimes(2);
	});

	it("does not count a report that arrives while the next test is waiting", async () => {
		const { monitor, check, banners } = setup(scripted("unreachable"));

		monitor.report("unreachable");
		await seconds(0);
		monitor.report("unreachable");
		monitor.report("unreachable");
		await seconds(0);

		expect(check).toHaveBeenCalledTimes(1);
		expect(visible(banners)[0]!.message).toMatchObject({ params: { attempts: 1 } });
	});

	it("counts the answer 200 as reachable: no warning, no further test", async () => {
		const { monitor, check, banners, unauthorized } = setup(scripted("ok"));

		monitor.report("unreachable");
		await seconds(60);

		expect(check).toHaveBeenCalledTimes(1);
		expect(visible(banners)).toEqual([]);
		expect(unauthorized).not.toHaveBeenCalled();
	});

	it("ends the testing at 401 or 407 (the check turns to the login page) and closes the warning", async () => {
		const { monitor, check, banners } = setup(scripted("unreachable", "unauthenticated"));

		monitor.report("unreachable");
		await seconds(0);
		expect(visible(banners)).toHaveLength(1);
		await seconds(5);
		await seconds(60);

		expect(check).toHaveBeenCalledTimes(2);
		expect(visible(banners)).toEqual([]);
	});

	it("counts an unexpected answer (404, 502) as a failed test", async () => {
		const { monitor, check, banners } = setup(scripted("unexpected"));

		monitor.report("unreachable");
		await seconds(5);

		expect(check).toHaveBeenCalledTimes(2);
		expect(visible(banners)[0]!.message).toMatchObject({ params: { attempts: 2 } });
	});

	it("hands unauthorized to the login without a test", async () => {
		const { monitor, check, unauthorized } = setup(scripted("ok"));

		monitor.report("unauthorized");
		await seconds(10);

		expect(unauthorized).toHaveBeenCalledOnce();
		expect(check).not.toHaveBeenCalled();
	});

	it("starts again with fresh counts after a recovery", async () => {
		const { monitor, banners } = setup(scripted("unreachable", "unreachable", "ok", "unreachable", "ok"));

		monitor.report("unreachable");
		await seconds(10); // Two failed tests, then success.
		expect(visible(banners)).toEqual([]);

		monitor.report("unreachable");
		await seconds(0);

		expect(visible(banners)[0]!.message).toMatchObject({ params: { attempts: 1 } });
	});
});

describe("connection monitor: the warning", () => {
	it("shows a warning without X and button, with title, number of failed tests, and time until the logout", async () => {
		const { monitor, banners } = setup(scripted("unreachable"));

		monitor.report("unreachable");
		await seconds(0);

		expect(visible(banners)).toEqual([
			{
				severity: "warning",
				dismissible: false,
				title: { key: "connection.title" },
				message: { key: "connection.messageMinutes", params: { attempts: 1, count: 5 } },
			},
		]);
	});

	it("raises the number with every failed test, in the same banner", async () => {
		const { monitor, banners } = setup(scripted("unreachable"));

		monitor.report("unreachable");
		await seconds(10);

		expect(banners.getSnapshot()).toHaveLength(1);
		expect(visible(banners)[0]!.message).toMatchObject({ params: { attempts: 3 } });
	});

	it("waits for failuresBeforeWarning failed tests", async () => {
		const { monitor, banners } = setup(scripted("unreachable"), { failuresBeforeWarning: 3 });

		monitor.report("unreachable");
		await seconds(0);
		expect(visible(banners)).toEqual([]);
		await seconds(5);
		expect(visible(banners)).toEqual([]);
		await seconds(5);

		expect(visible(banners)[0]!.message).toMatchObject({ params: { attempts: 3 } });
	});

	it("keeps testing while the warning is shown, and closes it when a test works", async () => {
		const { monitor, banners } = setup(scripted("unreachable", "unreachable", "ok"));

		monitor.report("unreachable");
		await seconds(5);
		expect(visible(banners)).toHaveLength(1);
		await seconds(5);

		expect(visible(banners)).toEqual([]);
	});

	it.each([
		[300, "connection.messageMinutes", 5],
		[120, "connection.messageMinutes", 2],
		[119, "connection.messageSeconds", 119],
		[20, "connection.messageSeconds", 20],
	])("names a logout after %i s as %s with the count %i", async (logoutAfterSeconds, key, count) => {
		const { monitor, banners } = setup(scripted("unreachable"), { logoutAfterSeconds });

		monitor.report("unreachable");
		await seconds(0);

		expect(visible(banners)[0]!.message).toEqual({ key, params: { attempts: 1, count } });
	});
});

describe("connection monitor: the logout", () => {
	it("logs out locally once the test has not worked for logoutAfterSeconds, counted from the first failed test", async () => {
		const { monitor, check, unauthorized } = setup(scripted("unreachable"), { logoutAfterSeconds: 20 });

		monitor.report("unreachable");
		await seconds(19);
		expect(unauthorized).not.toHaveBeenCalled();
		await seconds(1);

		expect(unauthorized).toHaveBeenCalledOnce();
		expect(check).toHaveBeenCalledTimes(5);
	});

	it("tests no more after the logout, and closes the warning", async () => {
		const { monitor, check, banners } = setup(scripted("unreachable"), { logoutAfterSeconds: 20 });

		monitor.report("unreachable");
		await seconds(20);
		const calls = check.mock.calls.length;
		await seconds(120);

		expect(check).toHaveBeenCalledTimes(calls);
		expect(visible(banners).some((request) => request.severity === "warning")).toBe(false);
	});

	it("shows the notice on the login page as an info with X, after the banners of the work are cleared", async () => {
		const banners = createBanners();
		// Like `startApp`: the logout clears all banners at once.
		const unauthorized = vi.fn(() => banners.clear());
		const monitor = createConnectionMonitor({
			auth: { check: scripted("unreachable"), unauthorized },
			banners,
			settings: { logoutAfterSeconds: 20 },
		});

		monitor.report("unreachable");
		await seconds(20);

		expect(unauthorized).toHaveBeenCalledOnce();
		expect(visible(banners)).toEqual([{ severity: "info", message: { key: "connection.loggedOut" } }]);
	});

	it("starts the clock again after a jump in time, for example after the computer slept", async () => {
		const { monitor, banners, unauthorized } = setup(scripted("unreachable"), { logoutAfterSeconds: 20 });

		monitor.report("unreachable");
		await seconds(5);
		// The computer sleeps for an hour; the timer fires only after waking up.
		vi.setSystemTime(Date.now() + 3_600_000);
		await seconds(5);

		expect(unauthorized).not.toHaveBeenCalled();
		// The count stays; only the clock starts again.
		expect(visible(banners)[0]!.message).toMatchObject({ params: { attempts: 3 } });
		await seconds(19);
		expect(unauthorized).not.toHaveBeenCalled();
		await seconds(1);
		expect(unauthorized).toHaveBeenCalledOnce();
	});

	it("forgets the clock when a test works", async () => {
		const { monitor, unauthorized } = setup(scripted("unreachable", "unreachable", "ok", "unreachable"), { logoutAfterSeconds: 20 });

		monitor.report("unreachable");
		await seconds(10); // failed, failed, success
		monitor.report("unreachable");
		await seconds(18);

		expect(unauthorized).not.toHaveBeenCalled();
	});
});

describe("connection monitor: waiting for the backend at the start", () => {
	it("returns at once and shows nothing when the backend answers", async () => {
		const { monitor, banners, check } = setup(scripted("ok"));

		await monitor.waitForBackend();

		expect(check).toHaveBeenCalledOnce();
		expect(visible(banners)).toEqual([]);
	});

	it("shows the start warning (no sentence about a logout), tests every interval, and goes on when the backend answers", async () => {
		const { monitor, banners, check } = setup(scripted("unreachable", "unexpected", "ok"));
		const done = vi.fn();

		void monitor.waitForBackend().then(done);
		await seconds(0);
		expect(visible(banners)).toEqual([
			{
				severity: "warning",
				dismissible: false,
				title: { key: "connection.title" },
				message: { key: "connection.startMessage", params: { attempts: 1 } },
			},
		]);
		expect(done).not.toHaveBeenCalled();

		await seconds(5);
		expect(visible(banners)[0]!.message).toMatchObject({ params: { attempts: 2 } });
		expect(done).not.toHaveBeenCalled();
		await seconds(5);

		expect(check).toHaveBeenCalledTimes(3);
		expect(done).toHaveBeenCalledOnce();
		expect(visible(banners)).toEqual([]);
	});

	it("goes on when the backend answers 401 or 407", async () => {
		const { monitor, banners } = setup(scripted("unreachable", "unauthenticated"));
		const done = vi.fn();

		void monitor.waitForBackend().then(done);
		await seconds(5);

		expect(done).toHaveBeenCalledOnce();
		expect(visible(banners)).toEqual([]);
	});

	it("gives the time limit to every test", async () => {
		const { monitor, check } = setup(scripted("unreachable", "ok"), { retryIntervalSeconds: 8 });

		void monitor.waitForBackend();
		await seconds(8);

		expect(check.mock.calls).toEqual([[{ timeoutMs: 8_000 }], [{ timeoutMs: 8_000 }]]);
	});

	it("never ends and never logs out", async () => {
		const { monitor, unauthorized } = setup(scripted("unreachable"), { logoutAfterSeconds: 20 });
		const done = vi.fn();

		void monitor.waitForBackend().then(done);
		await seconds(3_600);

		expect(done).not.toHaveBeenCalled();
		expect(unauthorized).not.toHaveBeenCalled();
	});

	it("waits for failuresBeforeWarning failed tests before it shows the warning", async () => {
		const { monitor, banners } = setup(scripted("unreachable"), { failuresBeforeWarning: 2 });

		void monitor.waitForBackend();
		await seconds(0);
		expect(visible(banners)).toEqual([]);
		await seconds(5);

		expect(visible(banners)[0]!.message).toMatchObject({ params: { attempts: 2 } });
	});
});
