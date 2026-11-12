import { describe, expect, it } from "vitest";
import { buildTree } from "../../../../../../client/src/shared";
import { collapsibleIds, dropChange, filterMemos, filterTopics, groupByProject, hiddenTopics, targetTopics, toFlatNodes } from "../../../../../../client/src/plugins/memos/model";
import { memo, topic } from "../../../../../helpers/client/memosFixtures";

const all = new Set(["waiting", "due", "snoozed", "done", "dropped", "promoted"]);
const filters = (extra: Partial<Parameters<typeof filterMemos>[2]> = {}) => ({ shownStatuses: all, search: "", showArchivedTopics: false, ...extra });

//  a ── b ── c        (c is deeper than the marked levels)
//   └── memos n1 (in a), n2 (in c)
const topics = [topic("a"), topic("b", { parent_uid: "a" }), topic("c", { parent_uid: "b" }), topic("z")];
const memos = [memo("n1", { topic_uid: "a" }), memo("n2", { topic_uid: "c", status: "due" }), memo("n3"), memo("n4", { topic_uid: "z", status: "done", archived: true })];

describe("filterMemos", () => {
	it("keeps the memos whose status is shown and whose text matches", () => {
		expect(filterMemos(memos, topics, filters({ shownStatuses: new Set(["waiting"]) })).map((n) => n.uid)).toEqual(["n1", "n3"]);
		expect(filterMemos(memos, topics, filters({ search: "N2" })).map((n) => n.uid)).toEqual(["n2"]);
		expect(filterMemos(memos, topics, filters({ search: "memo n1" })).map((n) => n.uid)).toEqual(["n1"]);
	});

	it("hides memos in archived topics, with the sub-topics, unless they are shown", () => {
		const archived = [topic("a", { archived: true }), topic("b", { parent_uid: "a" }), topic("c", { parent_uid: "b" }), topic("z")];
		expect([...hiddenTopics(archived, false)].sort()).toEqual(["a", "b", "c"]);
		expect(hiddenTopics(archived, true).size).toBe(0);
		expect(filterMemos(memos, archived, filters()).map((n) => n.uid)).toEqual(["n3", "n4"]);
		expect(filterMemos(memos, archived, filters({ showArchivedTopics: true })).map((n) => n.uid)).toEqual(["n1", "n2", "n3", "n4"]);
	});
});

describe("filterTopics", () => {
	it("keeps every active topic, empty ones too, when nothing is searched", () => {
		expect(filterTopics(topics, [], filters()).map((t) => t.uid)).toEqual(["a", "b", "c", "z"]);
	});

	it("keeps with a search the topics that match and the topics on the way to a found memo", () => {
		const found = filterMemos(memos, topics, filters({ search: "n2" }));
		expect(filterTopics(topics, found, filters({ search: "n2" })).map((t) => t.uid)).toEqual(["a", "b", "c"]);
		const byName = filterTopics(topics, [], filters({ search: "topic z" }));
		expect(byName.map((t) => t.uid)).toEqual(["z"]);
	});
});

describe("toFlatNodes", () => {
	const nodes = toFlatNodes(topics, memos.slice(0, 3), true);
	const byId = Object.fromEntries(nodes.map((node) => [node.id, node]));

	it("counts the shown memos of a topic with its sub-topics", () => {
		expect([byId.a!.count, byId.b!.count, byId.c!.count, byId.z!.count]).toEqual([2, 1, 1, 0]);
	});

	it("marks the first level as area 1 and everything deeper as area 2, with the memos in it", () => {
		expect([byId.a!.area, byId.b!.area, byId.c!.area]).toEqual([1, 2, 2]);
		expect([byId.n1!.area, byId.n2!.area, byId.n3!.area]).toEqual([1, 2, undefined]);
		expect(toFlatNodes(topics, memos, false).every((node) => node.area === undefined)).toBe(true);
	});

	it("hangs memos below their topic, those without below the root, and tags them", () => {
		expect([byId.n1!.parentId, byId.n3!.parentId, byId.b!.parentId]).toEqual(["a", null, "a"]);
		expect([byId.a!.tag, byId.n1!.tag]).toEqual(["Topic", "Memo"]);
	});

	it("puts siblings with due memos first, topics before memos, then by label", () => {
		const mixed = toFlatNodes([topic("t1"), topic("t2", { due_memos: 1 })], [memo("n1"), memo("n2", { status: "due" })], true);
		expect(mixed.map((node) => node.id)).toEqual(["t2", "n2", "t1", "n1"]);
		expect(buildTree(mixed).map((node) => node.id)).toEqual(["t2", "n2", "t1", "n1"]);
	});

	it("draws archived nodes dashed", () => {
		const archived = toFlatNodes([topic("a", { archived: true })], [memo("n", { archived: true })], true);
		expect(archived.every((node) => node.dashed)).toBe(true);
	});
});

describe("collapsibleIds", () => {
	it("names the topics that have children", () => {
		expect(collapsibleIds(topics, memos).sort()).toEqual(["a", "b", "c", "z"]);
		expect(collapsibleIds([topic("empty")], [])).toEqual([]);
	});
});

describe("dropChange", () => {
	it("puts a memo into a topic when dropped inside it", () => {
		expect(dropChange(topics, memos, "n3", "a", "inside")).toEqual({ kind: "memo", uid: "n3", version: 1, topic: "a" });
	});

	it("puts a memo next to a topic below the topic's parent, and next to a memo into that memo's topic", () => {
		expect(dropChange(topics, memos, "n3", "b", "before")).toEqual({ kind: "memo", uid: "n3", version: 1, topic: "a" });
		expect(dropChange(topics, memos, "n3", "n2", "after")).toEqual({ kind: "memo", uid: "n3", version: 1, topic: "c" });
		expect(dropChange(topics, memos, "n1", "n3", "after")).toEqual({ kind: "memo", uid: "n1", version: 1, topic: null });
	});

	it("moves a topic below another topic or next to it", () => {
		expect(dropChange(topics, memos, "z", "a", "inside")).toEqual({ kind: "topic", uid: "z", version: 1, parent: "a" });
		expect(dropChange(topics, memos, "c", "z", "after")).toEqual({ kind: "topic", uid: "c", version: 1, parent: null });
	});

	it("takes a node to the project with a null target", () => {
		expect(dropChange(topics, memos, "n1", null, "inside", "p1")).toEqual({ kind: "memo", uid: "n1", version: 1, topic: null });
		expect(dropChange(topics, memos, "b", null, "inside", "p1")).toEqual({ kind: "topic", uid: "b", version: 1, parent: null });
		expect(dropChange(topics, memos, "n1", null, "inside", "other")).toBeNull();
	});

	it("refuses what changes nothing or cannot work", () => {
		expect(dropChange(topics, memos, "n1", "a", "inside")).toBeNull(); // already there
		expect(dropChange(topics, memos, "a", "c", "inside")).toBeNull(); // into its own subtree
		expect(dropChange(topics, memos, "a", "c", "after")).toBeNull(); // next to a descendant
		expect(dropChange(topics, memos, "n3", "n1", "inside")).toBeNull(); // a memo is no container
		expect(dropChange(topics, memos, "n3", "n3", "after")).toBeNull();
		expect(dropChange(topics, memos, "nope", "a", "inside")).toBeNull();
		expect(dropChange(topics, [memo("x", { project_uid: "other" })], "x", "a", "inside")).toBeNull(); // other project
		expect(dropChange([topic("arch", { archived: true })], [memo("x")], "x", "arch", "inside")).toBeNull();
		expect(dropChange([topic("s", { system: true }), topic("a")], [], "s", "a", "inside")).toBeNull();
	});
});

describe("groupByProject and targetTopics", () => {
	it("groups by project in the order of the projects, keeping empty projects for their buttons", () => {
		const projects = [{ uid: "p0" }, { uid: "p1" }];
		const groups = groupByProject(projects, topics, memos);
		expect(groups.map((g) => [g.project.uid, g.topics.length, g.memos.length])).toEqual([["p0", 0, 0], ["p1", 4, 4]]);
	});

	it("offers active topics of the project except the topic itself and everything below it", () => {
		expect(targetTopics([...topics, topic("arch", { archived: true })], "p1", "b").map((t) => t.uid)).toEqual(["a", "z"]);
		expect(targetTopics(topics, "p1").map((t) => t.uid)).toEqual(["a", "b", "c", "z"]);
		expect(targetTopics(topics, "other")).toEqual([]);
	});
});
