import { describe, expect, it } from "vitest";
import { parseViewKey, parseViewPath, viewKey, viewPath } from "../../../../../../client/src/core/navigation/paths";
import { coreTestIds } from "../../../../../../client/src/core/testIds";

describe("viewPath", () => {
	it("builds the path of a main route from owner and name", () => {
		expect(viewPath("example", "overview")).toBe("/example/overview");
	});

	it("builds the path of a view of the core", () => {
		expect(viewPath("core", "patients")).toBe("/core/patients");
	});

});

describe("viewKey and parseViewKey", () => {
	it("writes a view as <owner id>/<name>, the form used in the app config", () => {
		expect(viewKey("example", "overview")).toBe("example/overview");
	});

	it("reads a view key back into owner and name", () => {
		expect(parseViewKey("example-addon/panel")).toEqual({ ownerId: "example-addon", name: "panel" });
	});

	it.each([["example"], ["example/overview/more"], ["/example/overview"], [""]])("rejects '%s' as a view key", (key) => {
		expect(parseViewKey(key)).toBeUndefined();
	});
});

describe("parseViewPath", () => {
	it("splits a path into owner and name", () => {
		expect(parseViewPath("/example/overview")).toEqual({ ownerId: "example", name: "overview", rest: [] });
	});

	it("returns the remaining parts for deeper paths", () => {
		expect(parseViewPath("/example/hub/example-addon/panel")).toEqual({
			ownerId: "example",
			name: "hub",
			rest: ["example-addon", "panel"],
		});
	});

	it("ignores a trailing slash", () => {
		expect(parseViewPath("/example/overview/")).toEqual({ ownerId: "example", name: "overview", rest: [] });
	});

	it("returns only the owner for a path of one part", () => {
		expect(parseViewPath("/example")).toEqual({ ownerId: "example", name: undefined, rest: [] });
	});

	it("returns nothing for the root path", () => {
		expect(parseViewPath("/")).toBeUndefined();
	});
});

describe("coreTestIds for navigation", () => {
	it("builds the id of a tab from the identity of its contribution", () => {
		expect(coreTestIds.navTab("example", "overview")).toBe("core.nav-tab.example.overview");
	});

	it("builds the id of a sidebar section from the identity of its contribution", () => {
		expect(coreTestIds.sidebarSection("workspace", "projects")).toBe("core.sidebar-section.workspace.projects");
	});

	it("has fixed ids for the sidebar and the detail column", () => {
		expect(coreTestIds).toMatchObject({ sidebar: "core.sidebar", detail: "core.detail" });
	});

	it("has fixed ids for the areas and notices", () => {
		expect(coreTestIds).toMatchObject({
			tabBar: "core.tab-bar",
			pageHeader: "core.page-header",
			content: "core.content",
			loading: "core.loading",
			noViews: "core.no-views",
			notFound: "core.not-found",
			unavailable: "core.unavailable",
			homeButton: "core.home-button",
		});
	});
});
