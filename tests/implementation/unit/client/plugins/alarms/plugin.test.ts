import { describe, expect, it, vi } from "vitest";
import { checkContributions } from "../../../../../../client/src/core/plugins/checkContributions";
import { checkDefinition } from "../../../../../../client/src/core/plugins/checkDefinition";
import { plugin } from "../../../../../../client/src/plugins/alarms";
import manifest from "../../../../../../client/src/plugins/alarms/plugin.json";

describe("alarms plugin definition", () => {
	it("puts its settings into the group system", () => {
		const settings = (plugin.contributions ?? []).filter((entry) => entry.slot === "core.settings-sections");
		expect(settings.map((entry) => ("group" in entry ? entry.group : undefined))).toEqual(["system"]);
	});

	it("is valid, needs the layout and the workspace, and hangs into the slots of others", () => {
		expect(checkDefinition({ plugin }, "alarms").ok).toBe(true);
		expect(checkContributions(plugin.contributions ?? [])).toEqual([]);
		expect(manifest.requires).toEqual(["layout-header-sidebar", "workspace"]);
		const widgets = (plugin.contributions ?? []).filter((entry) => entry.slot !== "core.main");
		expect(widgets.map((entry) => entry.slot).sort()).toEqual([
			"core.settings-sections",
			"workspace.attention-sources",
			"workspace.create-types",
			"workspace.detail-sections",
		]);
	});

	it.each([
		["alarms.alarm.changed", ["Alarms"]],
		["workspace.element.changed", ["Alarms"]],
		["core.reconnected", ["Alarms"]],
	])("reloads what changed on %s", (topic, tags) => {
		const dispatch = vi.fn();
		const invalidateTags = vi.fn((tags: string[]) => ({ type: "invalidate", tags }));

		plugin.eventHandlers![topic]!({}, { dispatch, api: { util: { invalidateTags } } as never });

		expect(dispatch).toHaveBeenCalledWith({ type: "invalidate", tags });
	});

	it("handles the event alarms.due", () => {
		expect(plugin.eventHandlers!["alarms.due"]).toBeTypeOf("function");
	});
});
