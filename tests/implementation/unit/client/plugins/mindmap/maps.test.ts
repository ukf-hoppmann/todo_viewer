import { describe, expect, it } from "vitest";
import { chooseMap, deleteQuestion, mapKey } from "../../../../../../client/src/plugins/mindmap/domain/maps";

const project = { project_uid: "p1", kind: "project", name: "Allgemein", tree_uid: "t1", node_count: 3, shared_count: 0, version: 1 };
const free = (uid: string, name: string, extra: object = {}) => ({ project_uid: "p1", kind: "free", name, tree_uid: uid, node_count: 0, shared_count: 0, version: 1, ...extra });

describe("chooseMap: the map of a project the page shows", () => {
	it("is the project tree when nothing was chosen", () => {
		expect(chooseMap([project, free("f1", "Ideen")], undefined)).toBe(project);
	});

	it("is the chosen free map", () => {
		const ideas = free("f1", "Ideen");
		expect(chooseMap([project, ideas], "f1")).toBe(ideas);
	});

	it("falls back to the project tree when the chosen map is gone (deleted)", () => {
		expect(chooseMap([project], "f1")).toBe(project);
	});

	it("does not choose the project tree by a stale uid of another project", () => {
		expect(chooseMap([project, free("f2", "Roadmap")], "other")).toBe(project);
	});

	it("is undefined while the list is not loaded", () => {
		expect(chooseMap(undefined, "f1")).toBeUndefined();
		expect(chooseMap([], undefined)).toBeUndefined();
	});
});

describe("mapKey", () => {
	it("is the tree uid, for a project tree without a node yet the project uid", () => {
		expect(mapKey(project)).toBe("t1");
		expect(mapKey({ ...project, tree_uid: null })).toBe("p1");
	});
});

describe("deleteQuestion: what the confirmation of deleting a free map says", () => {
	it("counts the nodes that go with the map and those that stay elsewhere", () => {
		expect(deleteQuestion(free("f1", "Ideen", { node_count: 5, shared_count: 2 }))).toEqual({ going: 3, kept: 2 });
	});

	it("keeps nothing when no node is shared", () => {
		expect(deleteQuestion(free("f1", "Ideen", { node_count: 4 }))).toEqual({ going: 4, kept: 0 });
	});
});
