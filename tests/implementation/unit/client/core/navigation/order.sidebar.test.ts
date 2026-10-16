import { describe, expect, it } from "vitest";
import { collectSidebarEntries, orderEntries } from "../../../../../../client/src/core/navigation/order";
import type { ActivePlugin, Contribution } from "../../../../../../client/src/core/plugins/types";

const icon = () => null;
const page = async () => ({ default: () => null });
const i18n = { de: {}, en: {}, fr: {} };

function entry(slot: string, name: string): Contribution {
	return { slot, name, title: `t.${name}`, icon, page };
}

function plugin(id: string, ...contributions: Contribution[]): ActivePlugin {
	return { id, definition: { i18n, contributions } };
}

function keys(entries: readonly { ownerId: string; name: string }[] | undefined): string[] {
	return (entries ?? []).map(({ ownerId, name }) => `${ownerId}/${name}`);
}

describe("collectSidebarEntries", () => {
	it("puts the entries of the host first, then those of other plugins by id, each in the order of its definition", () => {
		const plugins = [
			plugin("zeta", entry("example.hub", "z2"), entry("example.hub", "z1")),
			plugin("example", entry("example.hub", "start"), entry("example.hub", "second")),
			plugin("alpha", entry("example.hub", "a1")),
		];

		const slots = collectSidebarEntries(plugins, []);

		expect(keys(slots.get("example.hub"))).toEqual(["example/start", "example/second", "alpha/a1", "zeta/z2", "zeta/z1"]);
	});

	it("keeps the entries of different slots apart and describes where each hangs", () => {
		const slots = collectSidebarEntries([plugin("a", entry("a.one", "x"), entry("b.two", "y"))], []);

		expect([...slots.keys()].sort()).toEqual(["a.one", "b.two"]);
		expect(slots.get("b.two")?.[0]).toMatchObject({ ownerId: "a", name: "y", slot: "b.two", hostId: "b", hostName: "two" });
	});

	it("includes the entries of the core", () => {
		const slots = collectSidebarEntries([plugin("alpha", entry("core.patients", "a1"))], [entry("core.patients", "list")]);

		expect(keys(slots.get("core.patients"))).toEqual(["core/list", "alpha/a1"]);
	});

	it("ignores the tabs", () => {
		const tab: Contribution = { slot: "core.main", name: "overview", title: "t", icon, page };

		expect(collectSidebarEntries([plugin("alpha", tab)], []).size).toBe(0);
	});

	it("returns nothing for no plugins and no contributions", () => {
		expect(collectSidebarEntries([], []).size).toBe(0);
	});
});

describe("orderEntries for the entries of a sidebar", () => {
	const slots = collectSidebarEntries(
		[plugin("example", entry("example.hub", "start")), plugin("addon", entry("example.hub", "panel"))],
		[],
	);
	const entries = slots.get("example.hub") ?? [];

	it("keeps the fixed order without a list", () => {
		expect(keys(orderEntries(entries, undefined).ordered)).toEqual(["example/start", "addon/panel"]);
	});

	it("puts the listed entries first and reports unknown ones", () => {
		const { ordered, skipped } = orderEntries(entries, ["addon/panel", "ghost/view"]);

		expect(keys(ordered)).toEqual(["addon/panel", "example/start"]);
		expect(skipped).toEqual(["ghost/view"]);
	});
});
