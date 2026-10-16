import { describe, expect, it, vi } from "vitest";
import { checkContributions } from "../../../../../../client/src/core/plugins/checkContributions";
import { checkDefinition } from "../../../../../../client/src/core/plugins/checkDefinition";
import { plugin } from "../../../../../../client/src/plugins/workspace";
import manifest from "../../../../../../client/src/plugins/workspace/plugin.json";

describe("workspace plugin definition", () => {
	it("is a valid definition that hangs into the layout plugin and provides the create slot", () => {
		expect(checkDefinition({ plugin }, "workspace").ok).toBe(true);
		expect(checkContributions(plugin.contributions ?? [])).toEqual([]);
		expect(manifest.requires).toEqual(["layout-header-sidebar"]);
		expect(Object.keys(plugin.slots ?? {})).toEqual(["create-types"]);
		expect(plugin.contributions?.map((entry) => entry.slot)).toEqual([
			"layout-header-sidebar.sidebar-sections",
			"layout-header-sidebar.sidebar-sections",
			"layout-header-sidebar.header-actions",
		]);
	});

	it.each([
		["workspace.project.changed", ["Projects"]],
		["workspace.links.changed", ["Links"]],
		["core.reconnected", ["Projects", "Links"]],
	])("reloads what changed on %s", (topic, tags) => {
		const dispatch = vi.fn();
		const invalidateTags = vi.fn((tags: string[]) => ({ type: "invalidate", tags }));

		plugin.eventHandlers![topic]!({}, { dispatch, api: { util: { invalidateTags } } as never });

		expect(dispatch).toHaveBeenCalledWith({ type: "invalidate", tags });
	});
});
