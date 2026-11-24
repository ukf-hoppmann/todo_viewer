import { describe, expect, it } from "vitest";
import { branchRows, buildEntries, emptyChoice, relationTargets, type Choices } from "../../../../../../client/src/plugins/mindmap/domain/transferPlan";

const node = (uid: string, parent: string | null, position: number, title = uid, text: string | null = null) => ({ uid, label: uid.toUpperCase(), parent_uid: parent, position, title, text });

describe("Zeilen des Astes", () => {
	it("zeigt den Ast nach Position geordnet, Eltern vor Kindern, mit Tiefe", () => {
		const nodes = [node("a", null, 0), node("c", "a", 1), node("b", "a", 0), node("d", "b", 0), node("x", null, 1)];
		expect(branchRows(nodes, "a").map((row) => [row.node.uid, row.depth])).toEqual([["a", 0], ["b", 1], ["d", 2], ["c", 1]]);
	});
});

describe("Plan aus den Wahlen", () => {
	const nodes = [node("a", null, 0, "Ast", "Text A"), node("b", "a", 0, "Kind"), node("c", "a", 1, "Notiz", "Text C")];
	const choices = (changes: Choices): Choices => changes;

	it("beginnt ohne Wahl: nichts ist ausgewählt, Titel und Ziel schlagen den Knoten vor", () => {
		expect(emptyChoice(nodes[0]!)).toMatchObject({ kind: "skip", type: "", title: "Ast", goal: "Text A", criteria: "", parent: null, dependsOn: [] });
		expect(buildEntries(nodes, {})).toEqual([]);
	});

	it("nimmt nur Items und Memos auf und leitet nichts aus Ebene oder Tiefe ab", () => {
		const entries = buildEntries(
			nodes,
			choices({
				a: { ...emptyChoice(nodes[0]!), kind: "item", type: "Story", criteria: "1. Läuft" },
				b: { ...emptyChoice(nodes[1]!), kind: "item", type: "Task", criteria: "1. Fertig", parent: "a", dependsOn: ["EXISTING-1"] },
				c: { ...emptyChoice(nodes[2]!), kind: "memo", title: "Merken" },
			}),
		);
		expect(entries).toEqual([
			{ node: "a", kind: "item", type: "Story", title: "Ast", goal: "Text A", completion_criteria: "1. Läuft" },
			{ node: "b", kind: "item", type: "Task", title: "Kind", completion_criteria: "1. Fertig", parent: "a", depends_on: ["EXISTING-1"] },
			{ node: "c", kind: "memo", memo: { summary: "Merken", body: "Text C" } },
		]);
	});

	it("lässt leere Felder weg, damit der Server die Vorgaben des Knotens nimmt", () => {
		const [entry] = buildEntries(nodes, { b: { ...emptyChoice(nodes[1]!), kind: "item", type: "Task", title: "  ", goal: "", criteria: "" } });
		expect(entry).toEqual({ node: "b", kind: "item", type: "Task" });
	});

	it("bietet als Ziel der Beziehung nur andere Items des Plans und vorhandene Items an", () => {
		const targets = relationTargets(
			nodes,
			{ a: { ...emptyChoice(nodes[0]!), kind: "item" }, b: { ...emptyChoice(nodes[1]!), kind: "item", title: "Neu" }, c: { ...emptyChoice(nodes[2]!), kind: "memo" } },
			"b",
			[{ uid: "i1", label: "STORY-001", title: "Vorhanden" }],
		);
		expect(targets.map((entry) => entry.id)).toEqual(["a", "i1"]);
		expect(targets[0]).toMatchObject({ label: "A", title: "Ast" });
	});

	it("entfernt eine Beziehung zu einem Knoten, der kein Item mehr wird", () => {
		const entries = buildEntries(nodes, {
			a: { ...emptyChoice(nodes[0]!), kind: "memo" },
			b: { ...emptyChoice(nodes[1]!), kind: "item", type: "Task", parent: "a", dependsOn: ["a", "x1"] },
		});
		expect(entries[1]).toMatchObject({ node: "b", depends_on: ["x1"] });
		expect(entries[1]).not.toHaveProperty("parent");
	});
});
