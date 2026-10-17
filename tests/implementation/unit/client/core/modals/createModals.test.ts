import { describe, expect, it, vi } from "vitest";
import { createModals } from "../../../../../../client/src/core/modals/createModals";

function front(modals: ReturnType<typeof createModals>) {
	const pending = modals.getSnapshot();
	if (!pending) throw new Error("no pending modal");
	return pending;
}

function asAlert(pending: ReturnType<typeof front>) {
	if (pending.kind !== "alert") throw new Error(`expected alert, got ${pending.kind}`);
	return pending;
}

function asConfirm(pending: ReturnType<typeof front>) {
	if (pending.kind !== "confirm") throw new Error(`expected confirm, got ${pending.kind}`);
	return pending;
}

function asBody(pending: ReturnType<typeof front>) {
	if (pending.kind !== "confirmWithBody") throw new Error(`expected confirmWithBody, got ${pending.kind}`);
	return pending;
}

describe("createModals: alert", () => {
	it("has nothing pending at the start", () => {
		expect(createModals().getSnapshot()).toBeUndefined();
	});

	it("shows the request and resolves only when it is closed", async () => {
		const modals = createModals();
		const done = vi.fn();

		const promise = modals.alert({ severity: "error", message: "x" }).then(done);
		await Promise.resolve();

		expect(asAlert(front(modals)).request).toMatchObject({ severity: "error", message: "x" });
		expect(done).not.toHaveBeenCalled();

		asAlert(front(modals)).close();
		await promise;

		expect(done).toHaveBeenCalledTimes(1);
		expect(modals.getSnapshot()).toBeUndefined();
	});
});

describe("createModals: confirm", () => {
	it("resolves true when confirmed", async () => {
		const modals = createModals();
		const promise = modals.confirm({ message: "sure?" });

		asConfirm(front(modals)).answer(true);

		expect(await promise).toBe(true);
	});

	it("resolves false when cancelled", async () => {
		const modals = createModals();
		const promise = modals.confirm({});

		asConfirm(front(modals)).answer(false);

		expect(await promise).toBe(false);
	});
});

describe("createModals: confirmWithBody", () => {
	const body = () => null;

	it("resolves with the confirmation and the last data", async () => {
		const modals = createModals();
		const promise = modals.confirmWithBody({ initialData: { a: 1 }, body });

		asBody(front(modals)).answer(true, { a: 2 });

		expect(await promise).toEqual({ confirmed: true, data: { a: 2 } });
	});

	it("resolves with the last data when cancelled", async () => {
		const modals = createModals();
		const promise = modals.confirmWithBody({ initialData: { a: 1 }, body });

		asBody(front(modals)).answer(false, { a: 5 });

		expect(await promise).toEqual({ confirmed: false, data: { a: 5 } });
	});

	it("hands the request with its initial data to the display", () => {
		const modals = createModals();
		void modals.confirmWithBody({ initialData: { a: 1 }, body });

		expect(asBody(front(modals)).request.initialData).toEqual({ a: 1 });
	});
});

describe("createModals: queue", () => {
	it("shows requests one by one in the order they arrived", async () => {
		const modals = createModals();
		const first = modals.alert({ message: "1" });
		const second = modals.alert({ message: "2" });
		const third = modals.alert({ message: "3" });

		expect(asAlert(front(modals)).request.message).toBe("1");
		asAlert(front(modals)).close();
		await first;
		expect(asAlert(front(modals)).request.message).toBe("2");
		asAlert(front(modals)).close();
		await second;
		expect(asAlert(front(modals)).request.message).toBe("3");
		asAlert(front(modals)).close();
		await third;
		expect(modals.getSnapshot()).toBeUndefined();
	});

	it("mixes kinds in the order they arrived, without precedence", async () => {
		const modals = createModals();
		const order: string[] = [];
		void modals.confirm({}).then(() => order.push("confirm"));
		void modals.alert({}).then(() => order.push("alert"));
		void modals.confirmWithBody({ initialData: 0, body: () => null }).then(() => order.push("body"));

		expect(front(modals).kind).toBe("confirm");
		asConfirm(front(modals)).answer(true);
		await Promise.resolve();
		expect(front(modals).kind).toBe("alert");
		asAlert(front(modals)).close();
		await Promise.resolve();
		expect(front(modals).kind).toBe("confirmWithBody");
		asBody(front(modals)).answer(false, 0);
		await Promise.resolve();
		await Promise.resolve();

		expect(order).toEqual(["confirm", "alert", "body"]);
	});

	it("keeps identical alerts as separate dialogs", async () => {
		const modals = createModals();
		const done = vi.fn();
		void modals.alert({ message: "same" }).then(done);
		void modals.alert({ message: "same" }).then(done);
		void modals.alert({ message: "same" }).then(done);

		for (let i = 0; i < 3; i++) {
			asAlert(front(modals)).close();
			await Promise.resolve();
		}

		expect(done).toHaveBeenCalledTimes(3);
		expect(modals.getSnapshot()).toBeUndefined();
	});

	it("does not let a request overwrite another", async () => {
		const modals = createModals();
		const first = modals.confirm({ message: "1" });
		const second = modals.confirm({ message: "2" });

		asConfirm(front(modals)).answer(true);
		asConfirm(front(modals)).answer(false);

		expect(await first).toBe(true);
		expect(await second).toBe(false);
	});

	it("keeps requests made before any display is attached", () => {
		const modals = createModals();
		void modals.alert({ message: "early" });
		const listener = vi.fn();

		modals.subscribe(listener);

		expect(asAlert(front(modals)).request.message).toBe("early");
	});

	it("settles every promise exactly once", async () => {
		const modals = createModals();
		const done = vi.fn();
		const first = modals.confirm({}).then(done);
		void modals.confirm({}).then(done);
		const pending = asConfirm(front(modals));

		pending.answer(true);
		pending.answer(false);
		pending.answer(false);
		await first;

		expect(done).toHaveBeenCalledTimes(1);
		expect(done).toHaveBeenCalledWith(true);
		// The second request still waits; the repeated answers did not consume it.
		expect(front(modals).kind).toBe("confirm");
	});

	it("ignores a repeated close of an alert", async () => {
		const modals = createModals();
		const first = modals.alert({ message: "1" });
		void modals.alert({ message: "2" });
		const pending = asAlert(front(modals));

		pending.close();
		pending.close();
		await first;

		expect(asAlert(front(modals)).request.message).toBe("2");
	});
});

describe("createModals: store", () => {
	it("returns the same snapshot until something changes", () => {
		const modals = createModals();
		void modals.alert({});

		expect(modals.getSnapshot()).toBe(modals.getSnapshot());
	});

	it("notifies listeners when a request arrives and when one is settled", () => {
		const modals = createModals();
		const listener = vi.fn();
		modals.subscribe(listener);

		void modals.alert({});
		expect(listener).toHaveBeenCalledTimes(1);

		asAlert(front(modals)).close();
		expect(listener).toHaveBeenCalledTimes(2);
	});

	it("stops notifying after unsubscribe", () => {
		const modals = createModals();
		const listener = vi.fn();
		const unsubscribe = modals.subscribe(listener);

		unsubscribe();
		void modals.alert({});

		expect(listener).not.toHaveBeenCalled();
	});

	it("is independent per instance", () => {
		const first = createModals();
		const second = createModals();

		void first.alert({});

		expect(second.getSnapshot()).toBeUndefined();
	});
});
