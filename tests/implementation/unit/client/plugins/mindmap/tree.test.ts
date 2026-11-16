import { describe, expect, it } from "vitest";
import { defaultOpen, isOpen, shownProject, toggledFold, visibleNodes } from "../../../../../../client/src/plugins/mindmap/domain/tree";
import { node } from "../../../../../helpers/client/mindmapFixtures";

const nodes = [node("a"), node("b", null, 1), node("a1", "a"), node("a2", "a", 1), node("a11", "a1"), node("a111", "a11")];
const ids = (shown: ReturnType<typeof visibleNodes>) => shown.map((entry) => entry.id);

describe("visibleNodes", () => {
	it("shows the root and two levels below it when nothing was folded yet", () => {
		const shown = visibleNodes("p1", nodes, {});

		expect(ids(shown)).toEqual(["p1", "a", "a1", "a2", "b"]);
		expect(shown.map((entry) => entry.depth)).toEqual([0, 1, 2, 2, 1]);
		expect(shown.find((entry) => entry.id === "p1")).toMatchObject({ parentId: null, node: undefined, hasChildren: true, open: true });
		expect(shown.find((entry) => entry.id === "a1")).toMatchObject({ parentId: "a", hasChildren: true, open: false });
		expect(shown.find((entry) => entry.id === "a2")).toMatchObject({ hasChildren: false });
	});

	it("keeps the order of the siblings by their position, whatever the order of the list", () => {
		const shown = visibleNodes("p1", [node("y", null, 1), node("x", null, 0), node("x2", "x", 1), node("x1", "x", 0)], {});

		expect(ids(shown)).toEqual(["p1", "x", "x1", "x2", "y"]);
	});

	it("follows what the user opened and closed", () => {
		expect(ids(visibleNodes("p1", nodes, { a1: "open" }))).toEqual(["p1", "a", "a1", "a11", "a2", "b"]);
		expect(ids(visibleNodes("p1", nodes, { a: "closed" }))).toEqual(["p1", "a", "b"]);
		expect(ids(visibleNodes("p1", nodes, { p1: "closed" }))).toEqual(["p1"]);
	});

	it("shows only the root of a project without nodes", () => {
		expect(visibleNodes("p1", [], {})).toEqual([{ id: "p1", parentId: null, depth: 0, node: undefined, hasChildren: false, open: true }]);
	});

	it("leaves out nodes whose parent is not in the tree", () => {
		expect(ids(visibleNodes("p1", [node("a"), node("lost", "gone")], {}))).toEqual(["p1", "a"]);
	});
});

describe("fold", () => {
	it("is open by default down to the first level", () => {
		expect([0, 1, 2, 3].map(defaultOpen)).toEqual([true, true, false, false]);
		expect(isOpen({}, "x", 1)).toBe(true);
		expect(isOpen({ x: "closed" }, "x", 1)).toBe(false);
		expect(isOpen({ x: "open" }, "x", 5)).toBe(true);
	});

	it("stores only what differs from the default", () => {
		expect(toggledFold({}, "a", 1)).toEqual({ a: "closed" });
		expect(toggledFold({ a: "closed" }, "a", 1)).toEqual({});
		expect(toggledFold({ b: "open" }, "a1", 2)).toEqual({ b: "open", a1: "open" });
		expect(toggledFold({ a1: "open" }, "a1", 2)).toEqual({});
	});
});

describe("shownProject", () => {
	const p1 = { uid: "p1" };
	const p2 = { uid: "p2" };

	it("is the marked project, else the only visible one, else none", () => {
		expect(shownProject([p1, p2], p2)).toBe(p2);
		expect(shownProject([p1], undefined)).toBe(p1);
		expect(shownProject([p1, p2], undefined)).toBeUndefined();
		expect(shownProject([], undefined)).toBeUndefined();
	});
});
