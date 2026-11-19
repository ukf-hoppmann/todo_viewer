import { describe, expect, it, vi } from "vitest";
import { activePluginIds } from "../../../../../../client/src/app/plugins/activePlugins";
import { checkContributions } from "../../../../../../client/src/core/plugins/checkContributions";
import { checkDefinition } from "../../../../../../client/src/core/plugins/checkDefinition";
import { plugin } from "../../../../../../client/src/plugins/mindmap";
import manifest from "../../../../../../client/src/plugins/mindmap/plugin.json";

describe("mindmap plugin definition", () => {
	it("is valid, switched on, and needs the layout, the workspace and the backlog", () => {
		expect(checkDefinition({ plugin }, "mindmap").ok).toBe(true);
		expect(checkContributions(plugin.contributions ?? [])).toEqual([]);
		expect(manifest.requires).toEqual(["layout-header-sidebar", "workspace", "backlog"]);
		expect(activePluginIds).toContain("mindmap");
	});

	it("has the main route with sidebar and detail column", () => {
		const routes = (plugin.contributions ?? []).filter((entry) => entry.slot === "core.main");
		expect(routes).toHaveLength(1);
		expect(routes[0]).toMatchObject({ name: "main", title: "tab.mindmap", layout: { sidebar: true, detail: true } });
	});

	it.each([
		["mindmap.node.changed", ["Tree", "Content", "ItemNode", "Maps"]],
		["mindmap.map.changed", ["Maps", "Tree", "Content", "ItemNode"]],
		["workspace.element.changed", ["Tree", "Content", "ItemNode", "Maps"]],
		["backlog.item.changed", ["Tree", "Content", "ItemNode"]],
		["memos.memo.changed", ["Content"]],
		["mindmap.document.changed", ["Tree", "Documents"]],
		["core.reconnected", ["Tree", "Documents", "Content", "ItemNode", "Maps"]],
	])("reloads on %s", (topic, tags) => {
		const dispatch = vi.fn();
		const invalidateTags = vi.fn((names: string[]) => ({ type: "invalidate", tags: names }));

		plugin.eventHandlers![topic]!({}, { dispatch, api: { util: { invalidateTags } } as never });

		expect(dispatch).toHaveBeenCalledWith({ type: "invalidate", tags });
	});
});
