import { describe, expect, it, vi } from "vitest";
import { checkContributions } from "../../../../../../client/src/core/plugins/checkContributions";
import { checkDefinition } from "../../../../../../client/src/core/plugins/checkDefinition";
import { plugin } from "../../../../../../client/src/plugins/workspace";
import manifest from "../../../../../../client/src/plugins/workspace/plugin.json";

describe("workspace plugin definition", () => {
	it("puts its settings into the groups projects and system", () => {
		const settings = (plugin.contributions ?? []).filter((entry) => entry.slot === "core.settings-sections");
		expect(settings.map((entry) => [entry.name, "group" in entry ? entry.group : undefined])).toEqual([
			["projects", "projects"],
			["auto-sync", "system"],
		]);
	});

	it("is a valid definition that hangs into the layout plugin and provides the create slot", () => {
		expect(checkDefinition({ plugin }, "workspace").ok).toBe(true);
		expect(checkContributions(plugin.contributions ?? [])).toEqual([]);
		expect(manifest.requires).toEqual(["layout-header-sidebar"]);
		expect(Object.keys(plugin.slots ?? {})).toEqual(["detail-sections", "element-detail", "attention-sources", "create-types"]);
		expect(plugin.contributions?.map((entry) => entry.slot)).toEqual([
			"core.main",
			"core.sidebar-sections",
			"core.sidebar-sections",
			"layout-header-sidebar.header-actions",
			"core.settings-sections",
			"core.settings-sections",
		]);
	});

	it.each([
		["workspace.project.changed", ["Projects"]],
		["workspace.links.changed", ["Links"]],
		["workspace.element.changed", ["Trash", "Links"]],
		["core.sync.state", ["Sync", "Projects"]],
		["core.settings.changed", ["SyncSettings"]],
		["core.reconnected", ["Projects", "Links", "Trash", "Sync", "SyncSettings"]],
	])("reloads what changed on %s", (topic, tags) => {
		const dispatch = vi.fn();
		const invalidateTags = vi.fn((tags: string[]) => ({ type: "invalidate", tags }));

		plugin.eventHandlers![topic]!({}, { dispatch, api: { util: { invalidateTags } } as never });

		expect(dispatch).toHaveBeenCalledWith({ type: "invalidate", tags });
	});
});
