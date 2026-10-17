import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createConnectionMonitor } from "../../../../../../client/src/core/backend/createConnectionMonitor";
import { BackendUnreachableError, type ConnectionSettings } from "../../../../../../client/src/core/backend/types";
import { createBanners } from "../../../../../../client/src/core/banners/createBanners";

type Outcome = "ok" | "unreachable" | "unexpected";
type Check = (options: { timeoutMs: number }) => Promise<void>;

/** A `check` that answers with the outcomes in turn; the last one repeats. */
function scripted(...outcomes: Outcome[]) {
	let index = 0;
	return vi.fn<Check>(async () => {
		const outcome = outcomes[Math.min(index++, outcomes.length - 1)]!;
		if (outcome === "unreachable") throw new BackendUnreachableError();
		if (outcome === "unexpected") throw new Error("scripted");
	});
}

/** A `check` whose answers the test hands out by hand. */
function held() {
	const pending: Array<() => void> = [];
	const check = vi.fn<Check>(
		() =>
			new Promise<void>((resolve) => {
				pending.push(resolve);
			}),
	);
	return { check, answer: () => pending.shift()!() };
}

function setup(check: ReturnType<typeof scripted>, settings?: Partial<ConnectionSettings>) {
	const banners = createBanners();
	const onRecovered = vi.fn();
	const monitor = createConnectionMonitor({ check, banners, settings, onRecovered });
	return { banners, monitor, check, onRecovered };
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

	it("never runs two tests at the same time", async () => {
		const { check, answer } = held();
		const monitor = createConnectionMonitor({ check, banners: createBanners() });

		monitor.report("unreachable");
		monitor.report("unreachable");
		monitor.report("unreachable");
		await seconds(30);
		expect(check).toHaveBeenCalledTimes(1);

		answer();
		await seconds(0);
		monitor.report("unreachable");
		await seconds(0);
		expect(check).toHaveBeenCalledTimes(2);
	});

	it("shows nothing and tells nobody when the backend answers the test", async () => {
		const { monitor, banners, onRecovered } = setup(scripted("ok"));

		monitor.report("unreachable");
		await seconds(0);

		expect(visible(banners)).toEqual([]);
		expect(onRecovered).toHaveBeenCalledTimes(1);
	});

	it("warns after the first failed test, counts the attempts, and tests again after the interval", async () => {
		const { monitor, banners, check } = setup(scripted("unreachable"));

		monitor.report("unreachable");
		await seconds(0);

		expect(visible(banners)).toEqual([
			{
				severity: "warning",
				dismissible: false,
				title: { key: "connection.title" },
				message: { key: "connection.message", params: { attempts: 1 } },
			},
		]);
		await seconds(5);
		expect(check).toHaveBeenCalledTimes(2);
		expect(visible(banners)[0]!.message).toEqual({ key: "connection.message", params: { attempts: 2 } });
		expect(banners.getSnapshot()).toHaveLength(1);
	});

	it("waits for the configured number of failures before it warns", async () => {
		const { monitor, banners } = setup(scripted("unreachable"), { failuresBeforeWarning: 3 });

		monitor.report("unreachable");
		await seconds(0);
		await seconds(5);
		expect(visible(banners)).toEqual([]);
		await seconds(5);
		expect(banners.getSnapshot()).toHaveLength(1);
	});

	it("closes the warning, forgets the attempts, and reports the recovery when the backend answers again", async () => {
		const { monitor, banners, onRecovered } = setup(scripted("unreachable", "unreachable", "ok"));

		monitor.report("unreachable");
		await seconds(10);

		expect(visible(banners)).toEqual([]);
		expect(onRecovered).toHaveBeenCalledTimes(1);

		monitor.report("unreachable");
		await seconds(0);
		expect(onRecovered).toHaveBeenCalledTimes(2);
	});

	it("never logs anything out: it keeps testing for as long as the backend stays away", async () => {
		const { monitor, check } = setup(scripted("unreachable"));

		monitor.report("unreachable");
		await seconds(3_600);

		expect(check.mock.calls.length).toBeGreaterThan(100);
	});

	it("lets an unexpected error of the test through and allows a new test afterwards", async () => {
		const check = scripted("unexpected", "ok");
		const monitor = createConnectionMonitor({ check, banners: createBanners() });
		const unhandled: unknown[] = [];
		process.once("unhandledRejection", (reason) => unhandled.push(reason));

		monitor.report("unreachable");
		await seconds(0);
		monitor.report("unreachable");
		await seconds(0);

		expect(check).toHaveBeenCalledTimes(2);
	});
});

describe("connection monitor: waiting for the backend at the start", () => {
	it("returns at once when the backend answers", async () => {
		const { monitor, check, banners } = setup(scripted("ok"));

		await monitor.waitForBackend();

		expect(check).toHaveBeenCalledTimes(1);
		expect(visible(banners)).toEqual([]);
	});

	it("warns with the start message while the backend does not answer, and closes it afterwards", async () => {
		const { monitor, banners, check } = setup(scripted("unreachable", "unreachable", "ok"));

		const done = monitor.waitForBackend();
		await seconds(0);
		expect(visible(banners)).toEqual([
			{
				severity: "warning",
				dismissible: false,
				title: { key: "connection.title" },
				message: { key: "connection.startMessage", params: { attempts: 1 } },
			},
		]);
		await seconds(5);
		expect(visible(banners)[0]!.message).toEqual({ key: "connection.startMessage", params: { attempts: 2 } });
		await seconds(5);
		await done;

		expect(check).toHaveBeenCalledTimes(3);
		expect(visible(banners)).toEqual([]);
	});

	it("rejects on an unexpected error of the test", async () => {
		const { monitor } = setup(scripted("unexpected"));

		await expect(monitor.waitForBackend()).rejects.toThrow("scripted");
	});
});
