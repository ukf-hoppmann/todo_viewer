import { describe, expect, it, vi } from "vitest";
import { checkContributions } from "../../../../../../client/src/core/plugins/checkContributions";
import { checkDefinition } from "../../../../../../client/src/core/plugins/checkDefinition";
import { plugin } from "../../../../../../client/src/plugins/backlog";
import manifest from "../../../../../../client/src/plugins/backlog/plugin.json";

describe("backlog plugin definition", () => {
	it("is valid, needs the layout and the workspace, and hangs its filters into the sidebar on its own route only", () => {
		expect(checkDefinition({ plugin }, "backlog").ok).toBe(true);
		expect(checkContributions(plugin.contributions ?? [])).toEqual([]);
		expect(manifest.requires).toEqual(["layout-header-sidebar", "workspace"]);
		const widgets = (plugin.contributions ?? []).filter((entry) => entry.slot !== "core.main");
		const filters = widgets.filter((entry) => entry.slot === "core.sidebar-sections");
		expect(filters).toHaveLength(2);
		expect(filters.every((entry) => "when" in entry && entry.when?.[0] === "backlog/main")).toBe(true);
		expect(widgets.filter((entry) => entry.slot === "workspace.create-types").map((entry) => entry.name)).toEqual(["epic", "story", "task"]);
	});

	it.each([
		["workspace.element.changed", ["Items"]],
		["backlog.item.changed", ["Items"]],
		["backlog.document.changed", ["Items", "Documents"]],
		["core.reconnected", ["Items", "Documents"]],
	])("reloads what changed on %s", (topic, tags) => {
		const dispatch = vi.fn();
		const invalidateTags = vi.fn((tags: string[]) => ({ type: "invalidate", tags }));

		plugin.eventHandlers![topic]!({}, { dispatch, api: { util: { invalidateTags } } as never });

		expect(dispatch).toHaveBeenCalledWith({ type: "invalidate", tags });
	});
});
