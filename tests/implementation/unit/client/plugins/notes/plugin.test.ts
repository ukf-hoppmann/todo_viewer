import { describe, expect, it, vi } from "vitest";
import { checkContributions } from "../../../../../../client/src/core/plugins/checkContributions";
import { checkDefinition } from "../../../../../../client/src/core/plugins/checkDefinition";
import { plugin } from "../../../../../../client/src/plugins/notes";
import manifest from "../../../../../../client/src/plugins/notes/plugin.json";

describe("notes plugin definition", () => {
	it("is valid, needs the layout and the workspace, and hangs its filter into the sidebar on its own route only", () => {
		expect(checkDefinition({ plugin }, "notes").ok).toBe(true);
		expect(checkContributions(plugin.contributions ?? [])).toEqual([]);
		expect(manifest.requires).toEqual(["layout-header-sidebar", "workspace", "backlog"]);
		const widgets = (plugin.contributions ?? []).filter((entry) => entry.slot !== "core.main");
		const filters = widgets.filter((entry) => entry.slot === "core.sidebar-sections");
		expect(filters).toHaveLength(1);
		expect(filters.every((entry) => "when" in entry && entry.when?.[0] === "notes/main")).toBe(true);
		expect(widgets.filter((entry) => entry.slot === "workspace.create-types").map((entry) => entry.name)).toEqual(["note", "topic"]);
		expect(widgets.filter((entry) => entry.slot === "workspace.element-detail").map((entry) => entry.name)).toEqual(["note"]);
		expect(widgets.filter((entry) => entry.slot === "backlog.item-detail").map((entry) => entry.name)).toEqual(["notices", "demote"]);
		expect(widgets.filter((entry) => entry.slot === "workspace.attention-sources").map((entry) => entry.name)).toEqual(["due"]);
		expect(widgets.filter((entry) => entry.slot === "core.settings-sections").map((entry) => entry.name)).toEqual(["settings"]);
	});

	it.each([
		["workspace.element.changed", ["Notes", "Due"]],
		["notes.note.changed", ["Notes", "Due"]],
		["notes.topic.changed", ["Notes", "Due"]],
		["notes.due", ["Notes", "Due"]],
		["notes.document.changed", ["Notes", "Documents"]],
		["notes.settings.changed", ["Settings", "Notes", "Due"]],
		["core.reconnected", ["Notes", "Due", "Documents", "Settings"]],
	])("reloads what changed on %s", (topic, tags) => {
		const dispatch = vi.fn();
		const invalidateTags = vi.fn((tags: string[]) => ({ type: "invalidate", tags }));

		plugin.eventHandlers![topic]!({}, { dispatch, api: { util: { invalidateTags } } as never });

		expect(dispatch).toHaveBeenCalledWith({ type: "invalidate", tags });
	});
});
