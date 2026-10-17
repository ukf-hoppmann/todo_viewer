import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { banners, createBanners, useBanners } from "../../../../../../client/src/core";

describe("createBanners: list and handle", () => {
	it("lists the banners in the order in which they were shown, each with its request", () => {
		const list = createBanners();

		list.show({ message: "eins" });
		list.show({ message: "zwei", severity: "warning", title: "Achtung" });

		const shown = list.getSnapshot();
		expect(shown.map(({ request }) => request.message)).toEqual(["eins", "zwei"]);
		expect(shown[1]!.request).toMatchObject({ severity: "warning", title: "Achtung" });
	});

	it("gives every banner its own id", () => {
		const list = createBanners();

		list.show({ message: "eins" });
		list.show({ message: "zwei" });

		const [first, second] = list.getSnapshot();
		expect(first!.id).not.toBe(second!.id);
	});

	it("returns the same list as long as nothing changes, so that the display does not render again for nothing", () => {
		const list = createBanners();
		list.show({ message: "eins" });

		expect(list.getSnapshot()).toBe(list.getSnapshot());
	});

	it("starts with no banner", () => {
		expect(createBanners().getSnapshot()).toEqual([]);
	});

	it("tells the subscribers about each change, and no more after they unsubscribe", () => {
		const list = createBanners();
		const listener = vi.fn();
		const unsubscribe = list.subscribe(listener);

		const handle = list.show({ message: "eins" });
		handle.update({ message: "zwei" });
		handle.close();
		expect(listener).toHaveBeenCalledTimes(3);

		unsubscribe();
		list.show({ message: "drei" });
		expect(listener).toHaveBeenCalledTimes(3);
	});

	it("changes only the fields named in `update`, and gives a new list", () => {
		const list = createBanners();
		const handle = list.show({ message: "alt", severity: "info", title: "Titel" });
		const before = list.getSnapshot();

		handle.update({ message: { key: "x.y", params: { count: 2 } }, severity: "error" });

		const [shown] = list.getSnapshot();
		expect(shown!.request).toEqual({ message: { key: "x.y", params: { count: 2 } }, severity: "error", title: "Titel" });
		expect(shown!.id).toBe(before[0]!.id);
		expect(list.getSnapshot()).not.toBe(before);
	});

	it("removes only its own banner on `close`, which may be called more than once and tells the subscribers once", () => {
		const list = createBanners();
		const first = list.show({ message: "eins" });
		list.show({ message: "zwei" });
		const listener = vi.fn();
		list.subscribe(listener);

		first.close();
		first.close();

		expect(list.getSnapshot().map(({ request }) => request.message)).toEqual(["zwei"]);
		expect(listener).toHaveBeenCalledTimes(1);
	});

	it("ignores `update` after the banner was closed, and tells nobody", () => {
		const list = createBanners();
		const handle = list.show({ message: "eins" });
		handle.close();
		const listener = vi.fn();
		list.subscribe(listener);

		handle.update({ message: "zwei" });

		expect(list.getSnapshot()).toEqual([]);
		expect(listener).not.toHaveBeenCalled();
	});

	it("lets a handle change only its own banner", () => {
		const list = createBanners();
		const first = list.show({ message: "eins" });
		list.show({ message: "zwei" });

		first.update({ message: "geändert" });

		expect(list.getSnapshot().map(({ request }) => request.message)).toEqual(["geändert", "zwei"]);
	});

	it("gives a handle in the list that works like the one `show` returned", () => {
		const list = createBanners();
		list.show({ message: "eins" });

		list.getSnapshot()[0]!.handle.close();

		expect(list.getSnapshot()).toEqual([]);
	});

	it("keeps independent lists apart", () => {
		const one = createBanners();
		const two = createBanners();

		one.show({ message: "eins" });

		expect(two.getSnapshot()).toEqual([]);
	});
});

const messages = (list: ReturnType<typeof createBanners>) => list.getSnapshot().map(({ request }) => request.message);

describe("createBanners: limit and waiting banners", () => {
	it("shows at most 20 banners by default and lets the others wait", () => {
		const list = createBanners();

		for (let number = 1; number <= 22; number++) list.show({ message: `Banner ${number}` });

		expect(list.getSnapshot()).toHaveLength(20);
		expect(messages(list)[0]).toBe("Banner 1");
		expect(messages(list)[19]).toBe("Banner 20");
	});

	it("applies the limit given to `configure`", () => {
		const list = createBanners();
		list.configure({ maxVisible: 2 });

		list.show({ message: "eins" });
		list.show({ message: "zwei" });
		list.show({ message: "drei" });

		expect(messages(list)).toEqual(["eins", "zwei"]);
	});

	it("moves the oldest waiting banner up when a visible one closes", () => {
		const list = createBanners();
		list.configure({ maxVisible: 2 });
		const first = list.show({ message: "eins" });
		list.show({ message: "zwei" });
		list.show({ message: "drei" });
		list.show({ message: "vier" });

		first.close();

		expect(messages(list)).toEqual(["zwei", "drei"]);
	});

	it("lets waiting banners move up when the limit is raised", () => {
		const list = createBanners();
		list.configure({ maxVisible: 1 });
		list.show({ message: "eins" });
		list.show({ message: "zwei" });
		list.show({ message: "drei" });

		list.configure({ maxVisible: 3 });

		expect(messages(list)).toEqual(["eins", "zwei", "drei"]);
	});

	it("keeps the banners that are visible when the limit gets lower, and lets new ones wait until fewer are visible", () => {
		const list = createBanners();
		const first = list.show({ message: "eins" });
		const second = list.show({ message: "zwei" });
		list.show({ message: "drei" });
		list.configure({ maxVisible: 1 });
		list.show({ message: "vier" });

		expect(messages(list)).toEqual(["eins", "zwei", "drei"]);

		first.close();
		second.close();
		expect(messages(list)).toEqual(["drei"]);

		list.getSnapshot()[0]!.handle.close();
		expect(messages(list)).toEqual(["vier"]);
	});

	it("keeps the default when `configure` names no limit, and ignores a limit below 1 or one that is not a whole number", () => {
		const list = createBanners();

		list.configure({});
		list.configure({ maxVisible: 0 });
		list.configure({ maxVisible: 1.5 });
		for (let number = 1; number <= 21; number++) list.show({ message: `Banner ${number}` });

		expect(list.getSnapshot()).toHaveLength(20);
	});

	it("lets `update` and `close` work on a waiting banner, which never shows once closed", () => {
		const list = createBanners();
		list.configure({ maxVisible: 1 });
		const first = list.show({ message: "eins" });
		const second = list.show({ message: "zwei" });
		list.show({ message: "drei" });

		second.update({ message: "zwei, geändert" });
		second.close();
		first.close();

		expect(messages(list)).toEqual(["drei"]);
	});

	it("shows the changed text of a waiting banner when it moves up", () => {
		const list = createBanners();
		list.configure({ maxVisible: 1 });
		const first = list.show({ message: "eins" });
		const second = list.show({ message: "zwei" });

		second.update({ message: "zwei, geändert" });
		first.close();

		expect(messages(list)).toEqual(["zwei, geändert"]);
	});
});

describe("createBanners: clear", () => {
	it("closes all banners, visible and waiting, and tells the subscribers once", () => {
		const list = createBanners();
		list.configure({ maxVisible: 1 });
		list.show({ message: "eins" });
		list.show({ message: "zwei" });
		const listener = vi.fn();
		list.subscribe(listener);

		list.clear();

		expect(list.getSnapshot()).toEqual([]);
		expect(listener).toHaveBeenCalledTimes(1);
	});

	it("tells nobody when there is nothing to clear", () => {
		const list = createBanners();
		const listener = vi.fn();
		list.subscribe(listener);

		list.clear();

		expect(listener).not.toHaveBeenCalled();
	});

	it("makes the handles of the cleared banners behave as closed, also those of waiting ones", () => {
		const list = createBanners();
		list.configure({ maxVisible: 1 });
		const first = list.show({ message: "eins" });
		const second = list.show({ message: "zwei" });

		list.clear();
		first.update({ message: "neu" });
		second.update({ message: "neu" });
		first.close();

		expect(list.getSnapshot()).toEqual([]);
	});

	it("shows banners again after it, and a banner shown right after it is not cleared", () => {
		const list = createBanners();
		list.show({ message: "alt" });

		list.clear();
		list.show({ message: "neu" });

		expect(messages(list)).toEqual(["neu"]);
	});
});

describe("createBanners: autoHideMs", () => {
	beforeEach(() => {
		vi.useFakeTimers();
	});
	afterEach(() => {
		vi.useRealTimers();
	});

	it("closes a banner after `autoHideMs`", () => {
		const list = createBanners();
		list.show({ message: "eins", autoHideMs: 1000 });

		vi.advanceTimersByTime(999);
		expect(messages(list)).toEqual(["eins"]);

		vi.advanceTimersByTime(1);
		expect(messages(list)).toEqual([]);
	});

	it("keeps a banner without `autoHideMs` until it is closed", () => {
		const list = createBanners();
		list.show({ message: "eins" });

		vi.advanceTimersByTime(24 * 60 * 60 * 1000);

		expect(messages(list)).toEqual(["eins"]);
	});

	it("starts the time when the banner becomes visible, so a waiting banner does not run out", () => {
		const list = createBanners();
		list.configure({ maxVisible: 1 });
		const first = list.show({ message: "eins" });
		list.show({ message: "zwei", autoHideMs: 1000 });

		vi.advanceTimersByTime(5000);
		first.close();
		expect(messages(list)).toEqual(["zwei"]);

		vi.advanceTimersByTime(999);
		expect(messages(list)).toEqual(["zwei"]);
		vi.advanceTimersByTime(1);
		expect(messages(list)).toEqual([]);
	});

	it("lets the next waiting banner move up when one runs out", () => {
		const list = createBanners();
		list.configure({ maxVisible: 1 });
		list.show({ message: "eins", autoHideMs: 1000 });
		list.show({ message: "zwei" });

		vi.advanceTimersByTime(1000);

		expect(messages(list)).toEqual(["zwei"]);
	});

	it("starts the time again when `update` names `autoHideMs`", () => {
		const list = createBanners();
		const handle = list.show({ message: "eins", autoHideMs: 1000 });
		vi.advanceTimersByTime(800);

		handle.update({ autoHideMs: 1000 });
		vi.advanceTimersByTime(800);
		expect(messages(list)).toEqual(["eins"]);

		vi.advanceTimersByTime(200);
		expect(messages(list)).toEqual([]);
	});

	it("does not start the time again when `update` names other fields", () => {
		const list = createBanners();
		const handle = list.show({ message: "eins", autoHideMs: 1000 });
		vi.advanceTimersByTime(800);

		handle.update({ message: "zwei" });
		vi.advanceTimersByTime(200);

		expect(messages(list)).toEqual([]);
	});

	it("lets `update` give a banner a time, and take it away again", () => {
		const list = createBanners();
		const timed = list.show({ message: "eins" });
		const untimed = list.show({ message: "zwei", autoHideMs: 500 });

		timed.update({ autoHideMs: 500 });
		untimed.update({ autoHideMs: undefined });
		vi.advanceTimersByTime(500);

		expect(messages(list)).toEqual(["zwei"]);
	});

	it("stops the time when the banner is closed or cleared, so nothing happens later", () => {
		const list = createBanners();
		const closed = list.show({ message: "eins", autoHideMs: 1000 });
		list.show({ message: "zwei", autoHideMs: 1000 });
		closed.close();
		list.clear();
		const listener = vi.fn();
		list.subscribe(listener);

		vi.advanceTimersByTime(5000);

		expect(listener).not.toHaveBeenCalled();
		expect(vi.getTimerCount()).toBe(0);
	});
});

describe("useBanners", () => {
	it("gives the central object `banners`, as `useModals` does for the dialogs", () => {
		expect(useBanners()).toBe(banners);
	});
});
