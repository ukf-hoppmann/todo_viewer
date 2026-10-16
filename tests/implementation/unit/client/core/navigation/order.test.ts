import { describe, expect, it } from "vitest";
import { collectMainEntries, orderEntries, resolveStart } from "../../../../../../client/src/core/navigation/order";
import type { NavEntry } from "../../../../../../client/src/core/navigation/types";
import type { ActivePlugin, Contribution } from "../../../../../../client/src/core/plugins/types";

const icon = () => null;
const page = async () => ({ default: () => null });
const i18n = { de: {}, en: {}, fr: {} };

function tab(name: string): Contribution {
	return { slot: "core.main", name, title: `t.${name}`, icon, page };
}

function plugin(id: string, ...names: string[]): ActivePlugin {
	return { id, definition: { i18n, contributions: names.map(tab) } };
}

function keys(entries: readonly NavEntry[]): string[] {
	return entries.map(({ ownerId, name }) => `${ownerId}/${name}`);
}

describe("collectMainEntries", () => {
	it("puts the plugins first by id, each in the order of its definition, then the core", () => {
		const entries = collectMainEntries([plugin("zeta", "z2", "z1"), plugin("alpha", "a1")], [tab("patients")]);

		expect(keys(entries)).toEqual(["alpha/a1", "zeta/z2", "zeta/z1", "core/patients"]);
	});

	it("skips plugins without contributions", () => {
		const entries = collectMainEntries([{ id: "plain", definition: { i18n } }, plugin("alpha", "a1")], []);

		expect(keys(entries)).toEqual(["alpha/a1"]);
	});

	it("keeps the contribution with each entry", () => {
		const [entry] = collectMainEntries([plugin("alpha", "a1")], []);

		expect(entry).toMatchObject({ ownerId: "alpha", name: "a1", contribution: { title: "t.a1" } });
	});

	it("ignores contributions to other slots", () => {
		const other = { ...tab("x"), slot: "other.slot" } as unknown as Contribution;

		expect(collectMainEntries([{ id: "alpha", definition: { i18n, contributions: [other] } }], [])).toEqual([]);
	});

	it("returns an empty list for nothing", () => {
		expect(collectMainEntries([], [])).toEqual([]);
	});
});

describe("orderEntries", () => {
	const entries = collectMainEntries([plugin("alpha", "a1", "a2"), plugin("beta", "b1")], [tab("patients")]);

	it("keeps the fixed order without a list", () => {
		expect(keys(orderEntries(entries, undefined).ordered)).toEqual(["alpha/a1", "alpha/a2", "beta/b1", "core/patients"]);
	});

	it("puts the listed entries first in the order of the list, then the rest in the fixed order", () => {
		const { ordered } = orderEntries(entries, ["beta/b1", "alpha/a2"]);

		expect(keys(ordered)).toEqual(["beta/b1", "alpha/a2", "alpha/a1", "core/patients"]);
	});

	it("skips unknown or inactive entries of the list and reports them", () => {
		const { ordered, skipped } = orderEntries(entries, ["ghost/view", "beta/b1"]);

		expect(keys(ordered)).toEqual(["beta/b1", "alpha/a1", "alpha/a2", "core/patients"]);
		expect(skipped).toEqual(["ghost/view"]);
	});

	it("lists an entry once even if the list names it twice", () => {
		expect(keys(orderEntries(entries, ["beta/b1", "beta/b1"]).ordered)).toEqual(["beta/b1", "alpha/a1", "alpha/a2", "core/patients"]);
	});

	it("reports nothing when every entry of the list exists", () => {
		expect(orderEntries(entries, ["beta/b1"]).skipped).toEqual([]);
	});
});

describe("resolveStart", () => {
	const tabs = collectMainEntries([plugin("alpha", "a1"), plugin("beta", "b1")], []);
	const always = () => true;

	it("leads to the configured start view", () => {
		expect(resolveStart(tabs, "beta/b1", always)).toEqual({ to: "/beta/b1" });
	});

	it("leads to a sidebar entry when that is the start view", () => {
		expect(resolveStart(tabs, "alpha/hub/beta/panel", always)).toEqual({ to: "/alpha/hub/beta/panel" });
	});

	it("leads to the first tab without a start view", () => {
		expect(resolveStart(tabs, undefined, always)).toEqual({ to: "/alpha/a1" });
	});

	it("leads to the first tab and reports the start view when it is not available", () => {
		expect(resolveStart(tabs, "ghost/view", (path) => path !== "/ghost/view")).toEqual({
			to: "/alpha/a1",
			unavailableStart: "ghost/view",
		});
	});

	it("leads nowhere when there is no tab and no usable start view", () => {
		expect(resolveStart([], undefined, always)).toEqual({ to: undefined });
		expect(resolveStart([], "ghost/view", () => false)).toEqual({ to: undefined, unavailableStart: "ghost/view" });
	});
});
