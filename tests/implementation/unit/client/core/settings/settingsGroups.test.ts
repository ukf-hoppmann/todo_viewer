import { describe, expect, it } from "vitest";
import type { SlotEntry } from "../../../../../../client/src/core/plugins/useSlot";
import { defaultSettingsGroup, groupSettingsSections, isSettingsGroup, settingsGroups } from "../../../../../../client/src/core/settings/settingsGroups";

const Component = () => null;
const entry = (name: string, group?: string): SlotEntry => ({ ownerId: "a", name, component: Component, group });

describe("settingsGroups", () => {
	it("are projects and system, in this order", () => {
		expect(settingsGroups).toEqual(["projects", "system"]);
	});
});

describe("groupSettingsSections", () => {
	it("puts every section into its group and keeps the order of the slot", () => {
		const grouped = groupSettingsSections([entry("p1", "projects"), entry("s1", "system"), entry("p2", "projects")]);

		expect(grouped.projects.map((section) => section.name)).toEqual(["p1", "p2"]);
		expect(grouped.system.map((section) => section.name)).toEqual(["s1"]);
	});

	it("puts a section without a group or with an unknown group into system", () => {
		const grouped = groupSettingsSections([entry("none"), entry("odd", "other"), entry("p", "projects")]);

		expect(grouped.system.map((section) => section.name)).toEqual(["none", "odd"]);
		expect(grouped.projects.map((section) => section.name)).toEqual(["p"]);
	});

	it("returns an empty list for a group without sections", () => {
		expect(groupSettingsSections([])).toEqual({ projects: [], system: [] });
	});
});

describe("isSettingsGroup", () => {
	it("is true for a group of the core only", () => {
		expect(isSettingsGroup("system")).toBe(true);
		expect(isSettingsGroup("projects")).toBe(true);
		expect(isSettingsGroup("nope")).toBe(false);
		expect(isSettingsGroup(null)).toBe(false);
	});
});

describe("defaultSettingsGroup", () => {
	it("is the first group that has sections", () => {
		expect(defaultSettingsGroup(groupSettingsSections([entry("s", "system")]))).toBe("system");
		expect(defaultSettingsGroup(groupSettingsSections([entry("s", "system"), entry("p", "projects")]))).toBe("projects");
	});

	it("is the first group if no group has sections", () => {
		expect(defaultSettingsGroup(groupSettingsSections([]))).toBe("projects");
	});
});
