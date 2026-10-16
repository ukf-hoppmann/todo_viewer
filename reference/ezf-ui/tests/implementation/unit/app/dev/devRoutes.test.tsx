import { describe, expect, it } from "vitest";
import { DialogDemo } from "../../../../../src/app/dev/DialogDemo";
import { devRoutes } from "../../../../../src/app/dev/devRoutes";

describe("devRoutes", () => {
	it("offers the dialog demo at /dev/core/dialogs in development mode", () => {
		expect(devRoutes).toEqual([expect.objectContaining({ ownerId: "core", name: "dialogs" })]);
	});

	it("loads the dialog demo as the default export of the page", async () => {
		const [route] = devRoutes;

		const page = await route!.load();

		expect(page.default).toBe(DialogDemo);
	});
});
