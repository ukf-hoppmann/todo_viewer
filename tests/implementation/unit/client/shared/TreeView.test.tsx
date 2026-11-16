import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { buildTree, sharedTestIds, TreeView, type DropPosition, type TreeDrop, type TreeNode } from "../../../../../client/src/shared";

const flat = [
	{ id: "e1", parentId: null, label: "Epic", badge: "EPIC-1", statusColor: "red", progress: { done: 1, total: 2 } },
	{ id: "s1", parentId: "e1", label: "Story 1" },
	{ id: "t1", parentId: "s1", label: "Task" },
	{ id: "s2", parentId: "e1", label: "Story 2" },
	{ id: "e2", parentId: null, label: "Epic 2" },
];

interface HarnessProps {
	expanded?: string[];
	canDrop?: (source: TreeNode, target: TreeNode, position: DropPosition) => boolean;
	onDrop?: (drop: TreeDrop) => void;
	onSelect?: (id: string) => void;
	actions?: (node: TreeNode) => React.ReactNode;
}

function Harness({ expanded = [], canDrop, onDrop, onSelect, actions }: HarnessProps) {
	const [open, setOpen] = useState(new Set(expanded));
	const [selected, setSelected] = useState<string | null>(null);
	return (
		<TreeView
			ariaLabel="Backlog"
			nodes={buildTree(flat)}
			expanded={open}
			onToggle={(id) =>
				setOpen((current) => {
					const next = new Set(current);
					if (!next.delete(id)) next.add(id);
					return next;
				})
			}
			selectedId={selected}
			onSelect={(id) => {
				setSelected(id);
				onSelect?.(id);
			}}
			canDrop={canDrop}
			onDrop={onDrop}
			actions={actions}
		/>
	);
}

const node = (id: string) => screen.getByTestId(sharedTestIds.treeNode(id));
const visibleIds = () => screen.getAllByRole("treeitem").map((item) => item.getAttribute("data-testid")!.replace("shared.tree-node.", ""));

afterEach(cleanup);

describe("TreeView: structure", () => {
	it("shows the roots, and the children of open nodes, with levels and the open state", () => {
		render(<Harness expanded={["e1", "s1"]} />);

		expect(visibleIds()).toEqual(["e1", "s1", "t1", "s2", "e2"]);
		expect(node("e1").getAttribute("aria-level")).toBe("1");
		expect(node("t1").getAttribute("aria-level")).toBe("3");
		expect(node("e1").getAttribute("aria-expanded")).toBe("true");
		expect(node("s2").getAttribute("aria-expanded")).toBeNull();
		expect(screen.getByRole("tree", { name: "Backlog" })).toBeTruthy();
	});

	it("shows label, badge and a progress ring", () => {
		render(<Harness />);

		expect(node("e1").textContent).toContain("EPIC-1");
		expect(node("e1").textContent).toContain("Epic");
		expect(screen.getByTestId(sharedTestIds.progressRing).getAttribute("aria-label")).toBe("1/2");
	});

	it("draws a dashed node as dashed", () => {
		flat.push({ id: "opt", parentId: "e2", label: "Optional", dashed: true } as (typeof flat)[number]);
		try {
			render(<Harness expanded={["e2"]} />);

			expect(node("opt").getAttribute("data-dashed")).toBe("true");
			expect(node("e2").getAttribute("data-dashed")).toBeNull();
		} finally {
			flat.pop();
		}
	});

	it("shows a tag, a count and the area of a node", () => {
		flat.push({ id: "tag", parentId: "e2", label: "Mit Tag", tag: "Topic", count: 4, area: 1 } as (typeof flat)[number]);
		try {
			render(<Harness expanded={["e2"]} />);

			expect(screen.getByTestId(sharedTestIds.treeTag("tag")).textContent).toBe("Topic");
			expect(screen.getByTestId(sharedTestIds.treeCount("tag")).textContent).toBe("4");
			expect(node("tag").getAttribute("data-area")).toBe("1");
			expect(node("e2").getAttribute("data-area")).toBeNull();
			expect(screen.queryByTestId(sharedTestIds.treeCount("e2"))).toBeNull();
		} finally {
			flat.pop();
		}
	});

	it("opens and closes with the arrow button without selecting", () => {
		const onSelect = vi.fn();
		render(<Harness onSelect={onSelect} />);

		fireEvent.click(screen.getByTestId(sharedTestIds.treeToggle("e1")));
		expect(visibleIds()).toEqual(["e1", "s1", "s2", "e2"]);
		fireEvent.click(screen.getByTestId(sharedTestIds.treeToggle("e1")));
		expect(visibleIds()).toEqual(["e1", "e2"]);
		expect(onSelect).not.toHaveBeenCalled();
	});

	it("selects on click and marks the row", () => {
		render(<Harness />);

		fireEvent.click(node("e2"));

		expect(node("e2").getAttribute("aria-selected")).toBe("true");
		expect(node("e1").getAttribute("aria-selected")).toBe("false");
	});
});

describe("TreeView: keyboard", () => {
	const press = (id: string, key: string) => fireEvent.keyDown(node(id), { key });

	it("has one tab stop: the selected row, else the first", () => {
		render(<Harness expanded={["e1"]} />);
		expect(screen.getAllByRole("treeitem").filter((item) => item.tabIndex === 0).map((item) => item.getAttribute("data-testid"))).toEqual([
			"shared.tree-node.e1",
		]);

		fireEvent.click(node("s2"));
		expect(screen.getAllByRole("treeitem").filter((item) => item.tabIndex === 0).map((item) => item.getAttribute("data-testid"))).toEqual([
			"shared.tree-node.s2",
		]);
	});

	it("moves the focus with the arrow keys, Home and End", () => {
		render(<Harness expanded={["e1"]} />);
		node("e1").focus();

		press("e1", "ArrowDown");
		expect(document.activeElement).toBe(node("s1"));
		press("s1", "ArrowDown");
		expect(document.activeElement).toBe(node("s2"));
		press("s2", "ArrowUp");
		expect(document.activeElement).toBe(node("s1"));
		press("s1", "End");
		expect(document.activeElement).toBe(node("e2"));
		press("e2", "Home");
		expect(document.activeElement).toBe(node("e1"));
	});

	it("opens with arrow right, goes into the first child, closes with arrow left, goes to the parent", () => {
		render(<Harness />);
		node("e1").focus();

		press("e1", "ArrowRight");
		expect(visibleIds()).toEqual(["e1", "s1", "s2", "e2"]);
		press("e1", "ArrowRight");
		expect(document.activeElement).toBe(node("s1"));
		press("s1", "ArrowLeft");
		expect(document.activeElement).toBe(node("e1"));
		press("e1", "ArrowLeft");
		expect(visibleIds()).toEqual(["e1", "e2"]);
	});

	it("selects with Enter and Space", () => {
		const onSelect = vi.fn();
		render(<Harness onSelect={onSelect} />);

		press("e2", "Enter");
		press("e1", " ");

		expect(onSelect.mock.calls).toEqual([["e2"], ["e1"]]);
	});

	it("leaves other keys alone", () => {
		render(<Harness />);
		const notPrevented = fireEvent.keyDown(node("e1"), { key: "a" });
		expect(notPrevented).toBe(true);
	});
});

describe("TreeView: actions", () => {
	it("renders the actions of a row inside it, without selecting when they are clicked", () => {
		const onSelect = vi.fn();
		const onAction = vi.fn();
		render(<Harness onSelect={onSelect} actions={(n) => <button onClick={() => onAction(n.id)}>do {n.id}</button>} />);

		fireEvent.click(within(screen.getByTestId(sharedTestIds.treeActions("e2"))).getByText("do e2"));

		expect(onAction).toHaveBeenCalledWith("e2");
		expect(onSelect).not.toHaveBeenCalled();
	});
});

import { within } from "@testing-library/react";

/** jsdom has no layout: give the row a box so that the drop position can be computed. */
function dragEvent(type: "dragOver" | "drop", target: HTMLElement, offsetY: number) {
	vi.spyOn(target, "getBoundingClientRect").mockReturnValue({ top: 0, height: 40, bottom: 40, left: 0, right: 100, width: 100, x: 0, y: 0, toJSON: () => ({}) });
	const data = new Map<string, string>();
	const dataTransfer = { setData: (k: string, v: string) => data.set(k, v), getData: (k: string) => data.get(k) ?? "", effectAllowed: "", dropEffect: "" };
	// jsdom has no DragEvent: build the event by hand so that it carries the pointer position.
	const event = Object.assign(new Event(type.toLowerCase(), { bubbles: true, cancelable: true }), { clientY: offsetY, dataTransfer });
	return fireEvent(target, event);
}

describe("TreeView: drag and drop", () => {
	function start(id: string) {
		fireEvent.dragStart(node(id), { dataTransfer: { setData: () => {}, effectAllowed: "" } });
	}

	it("is not draggable without canDrop and onDrop", () => {
		render(<Harness />);
		expect(node("e1").getAttribute("draggable")).toBe("false");
	});

	it("drops before, after, and into a node by the place on the row", () => {
		const onDrop = vi.fn();
		render(<Harness expanded={["e1"]} canDrop={() => true} onDrop={onDrop} />);

		start("s2");
		dragEvent("drop", node("e2"), 2);
		start("s2");
		dragEvent("drop", node("e2"), 38);
		start("s2");
		dragEvent("drop", node("e2"), 20);

		expect(onDrop.mock.calls.map(([drop]) => drop)).toEqual([
			{ sourceId: "s2", targetId: "e2", position: "before" },
			{ sourceId: "s2", targetId: "e2", position: "after" },
			{ sourceId: "s2", targetId: "e2", position: "inside" },
		]);
	});

	it("asks canDrop with source, target and position, and drops nothing when it says no", () => {
		const onDrop = vi.fn();
		const canDrop = vi.fn(() => false);
		render(<Harness expanded={["e1"]} canDrop={canDrop} onDrop={onDrop} />);

		start("s2");
		dragEvent("dragOver", node("e2"), 20);
		dragEvent("drop", node("e2"), 20);

		expect(canDrop).toHaveBeenCalledWith(expect.objectContaining({ id: "s2" }), expect.objectContaining({ id: "e2" }), "inside");
		expect(onDrop).not.toHaveBeenCalled();
	});

	it("shows the marker for the place while dragging over a node that accepts it, and removes it afterwards", () => {
		render(<Harness canDrop={() => true} onDrop={() => {}} />);

		start("e2");
		dragEvent("dragOver", node("e1"), 2);
		expect(screen.getByTestId(sharedTestIds.treeDrop("e1", "before"))).toBeTruthy();
		dragEvent("dragOver", node("e1"), 38);
		expect(screen.getByTestId(sharedTestIds.treeDrop("e1", "after"))).toBeTruthy();
		fireEvent.dragEnd(node("e2"));
		expect(screen.queryByTestId(sharedTestIds.treeDrop("e1", "after"))).toBeNull();
	});

	it("does not allow a node to be dropped into its own subtree", () => {
		const onDrop = vi.fn();
		render(<Harness expanded={["e1", "s1"]} canDrop={() => true} onDrop={onDrop} />);

		start("e1");
		dragEvent("drop", node("t1"), 20);
		start("e1");
		dragEvent("drop", node("e1"), 20);

		expect(onDrop).not.toHaveBeenCalled();
	});
});

describe("TreeView: trailing", () => {
	it("shows the trailing content of a row inside a container that appears only while the pointer is on the row", () => {
		render(<TreeView ariaLabel="Backlog" nodes={buildTree(flat)} expanded={new Set()} onToggle={() => undefined} onSelect={() => undefined} trailing={(node) => <span data-testid={`mark.${node.id}`} />} />);

		const mark = screen.getByTestId("mark.e1");
		expect(screen.getByTestId(sharedTestIds.treeNode("e1")).contains(mark)).toBe(true);
		expect(mark.parentElement?.classList.contains("tree-actions")).toBe(true);
	});
});

describe("TreeView: drawing", () => {
	it("draws only the row that lost and the row that got the selection when a row is chosen", () => {
		const drawn: string[] = [];
		const nodes = buildTree(flat);
		const open = new Set(["e1", "s1"]);
		const trailing = (node: TreeNode) => {
			drawn.push(node.id);
			return null;
		};
		function Stable() {
			const [selected, setSelected] = useState<string | null>(null);
			return <TreeView ariaLabel="Backlog" nodes={nodes} expanded={open} onToggle={() => undefined} selectedId={selected} onSelect={setSelected} trailing={trailing} />;
		}
		render(<Stable />);
		fireEvent.click(node("s1"));
		drawn.length = 0;

		fireEvent.click(node("s2"));

		expect(drawn.sort()).toEqual(["s1", "s2"]);
	});
});
