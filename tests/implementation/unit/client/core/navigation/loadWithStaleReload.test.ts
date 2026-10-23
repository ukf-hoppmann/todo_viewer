import { beforeEach, describe, expect, it, vi } from "vitest";
import { loadWithStaleReload } from "../../../../../../client/src/core/navigation/loadWithStaleReload";

const stale = () => new TypeError("error loading dynamically imported module: http://x/assets/Old.js");

describe("loadWithStaleReload", () => {
	beforeEach(() => sessionStorage.clear());

	it("returns the module when the import works", async () => {
		const reload = vi.fn();
		await expect(loadWithStaleReload(async () => 1, reload)()).resolves.toBe(1);
		expect(reload).not.toHaveBeenCalled();
	});

	it("reloads once for a missing chunk and keeps the page pending", async () => {
		const reload = vi.fn();
		const result = await Promise.race([
			loadWithStaleReload(() => Promise.reject(stale()), reload)(),
			new Promise((resolve) => setTimeout(() => resolve("pending"), 20)),
		]);
		expect(result).toBe("pending");
		expect(reload).toHaveBeenCalledTimes(1);
	});

	it("passes the error on when the reload already happened", async () => {
		sessionStorage.setItem("stale-chunk-reloaded", "1");
		const reload = vi.fn();
		await expect(loadWithStaleReload(() => Promise.reject(stale()), reload)()).rejects.toThrow("dynamically");
		expect(reload).not.toHaveBeenCalled();
	});

	it("passes other errors on without reloading", async () => {
		const reload = vi.fn();
		await expect(loadWithStaleReload(() => Promise.reject(new Error("boom")), reload)()).rejects.toThrow("boom");
		expect(reload).not.toHaveBeenCalled();
	});
});
