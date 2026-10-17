import { describe, expect, it } from "vitest";
import { checkContributions } from "../../../../../../client/src/core/plugins/checkContributions";

const tab = (name: string) => ({ slot: "core.main", name, title: "t", icon: () => null, page: async () => ({ default: () => null }) });

describe("checkContributions: reserved names", () => {
	it("reports a name that is reserved for the owner", () => {
		expect(checkContributions([tab("login"), tab("overview")], { reservedNames: ["link", "login"] })).toEqual([
			"contribution 'login': the name is reserved",
		]);
	});

	it("allows every name when nothing is reserved", () => {
		expect(checkContributions([tab("login")])).toEqual([]);
	});

	it("returns no problems for undefined", () => {
		expect(checkContributions(undefined)).toEqual([]);
	});
});
