import { describe, expect, it, vi } from "vitest";
import { checkContributions } from "../../../../../../client/src/core/plugins/checkContributions";
import { checkDefinition } from "../../../../../../client/src/core/plugins/checkDefinition";
import { plugin } from "../../../../../../client/src/plugins/memos";
import manifest from "../../../../../../client/src/plugins/memos/plugin.json";

describe("memos plugin definition", () => {
	it("is valid, needs the layout and the workspace, and hangs its filter into the sidebar on its own route only", () => {
		expect(checkDefinition({ plugin }, "memos").ok).toBe(true);
		expect(checkContributions(plugin.contributions ?? [])).toEqual([]);
		expect(manifest.requires).toEqual(["layout-header-sidebar", "workspace", "backlog"]);
		const widgets = (plugin.contributions ?? []).filter((entry) => entry.slot !== "core.main");
		const filters = widgets.filter((entry) => entry.slot === "core.sidebar-sections");
		expect(filters).toHaveLength(1);
		expect(filters.every((entry) => "when" in entry && entry.when?.[0] === "memos/main")).toBe(true);
		expect(widgets.filter((entry) => entry.slot === "workspace.create-types").map((entry) => entry.name)).toEqual(["memo", "topic"]);
		expect(widgets.filter((entry) => entry.slot === "workspace.element-detail").map((entry) => entry.name)).toEqual(["memo"]);
		expect(widgets.filter((entry) => entry.slot === "backlog.item-detail").map((entry) => entry.name)).toEqual(["hints", "demote"]);
		expect(widgets.filter((entry) => entry.slot === "workspace.attention-sources").map((entry) => entry.name)).toEqual(["due"]);
		expect(widgets.filter((entry) => entry.slot === "core.settings-sections").map((entry) => entry.name)).toEqual(["settings"]);
	});

	it("puts its settings into the group system", () => {
		const settings = (plugin.contributions ?? []).filter((entry) => entry.slot === "core.settings-sections");
		expect(settings.map((entry) => ("group" in entry ? entry.group : undefined))).toEqual(["system"]);
	});

	it.each([
		["workspace.element.changed", ["Memos", "Due"]],
		["memos.memo.changed", ["Memos", "Due"]],
		["memos.topic.changed", ["Memos", "Due"]],
		["memos.due", ["Memos", "Due"]],
		["memos.document.changed", ["Memos", "Documents"]],
		["memos.settings.changed", ["Settings", "Memos", "Due"]],
		["core.reconnected", ["Memos", "Due", "Documents", "Settings"]],
	])("reloads what changed on %s", (topic, tags) => {
		const dispatch = vi.fn();
		const invalidateTags = vi.fn((tags: string[]) => ({ type: "invalidate", tags }));

		plugin.eventHandlers![topic]!({}, { dispatch, api: { util: { invalidateTags } } as never });

		expect(dispatch).toHaveBeenCalledWith({ type: "invalidate", tags });
	});
});
