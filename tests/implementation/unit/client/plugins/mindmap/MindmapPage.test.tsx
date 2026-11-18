import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { mindmapApi } from "../../../../../../client/src/plugins/mindmap/api";
import { LayoutSwitch } from "../../../../../../client/src/plugins/mindmap/LayoutSwitch";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { itemRef, node } from "../../../../../helpers/client/mindmapFixtures";
import { locationTestId } from "../../../../../helpers/client/locationTestId";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

// jsdom has no layout: React Flow is replaced by a list of the nodes it is given and a record of its edges.
vi.mock("@xyflow/react", () => {
	const Handle = (props: { type: string; id?: string }) => <span data-handle={`${props.type}-${props.id}`} />;
	return {
		Handle,
		Position: { Left: "left", Right: "right" },
		Background: () => null,
		Controls: () => null,
		ReactFlow: (props: {
			nodes: Array<{ id: string; type: string; data: unknown; position: { x: number; y: number } }>;
			edges: Array<{ id: string; sourceHandle?: string; targetHandle?: string }>;
			nodeTypes: Record<string, (props: { data: unknown }) => ReactNode>;
			onNodeClick: (event: unknown, node: { id: string }) => void;
			onNodeDoubleClick: (event: unknown, node: { id: string }) => void;
		}) => (
			<div data-testid="flow">
				{props.nodes.map((entry) => {
					const Node = props.nodeTypes[entry.type]!;
					return (
						<div key={entry.id} data-flow-node={entry.id} data-x={entry.position.x} data-y={entry.position.y} onClick={(event) => props.onNodeClick(event, entry)} onDoubleClick={(event) => props.onNodeDoubleClick(event, entry)}>
							<Node data={entry.data} />
						</div>
					);
				})}
				{props.edges.map((edge) => (
					<span key={edge.id} data-flow-edge={edge.id} data-source-handle={edge.sourceHandle} data-target-handle={edge.targetHandle} />
				))}
			</div>
		),
	};
});
vi.mock("@xyflow/react/dist/style.css", () => ({}));

const { default: MindmapPage } = await import("../../../../../../client/src/plugins/mindmap/pages/MindmapPage");

afterEach(cleanup);

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const nodes = [node("a"), node("b", null, 1), node("a1", "a"), node("a11", "a1")];
const marked = { workspace: { marked: "p1" } };

async function renderPage(options: Parameters<typeof fakeMindmapBackend>[0] = {}, address = "/mindmap/main") {
	const backend = fakeMindmapBackend({ projects, nodes, documents: marked, ...options });
	await renderWorkspace(<MindmapPage />, { backend, initialEntries: [address] });
	return backend;
}
const location = () => screen.getByTestId(locationTestId).textContent;
/** What the server event `mindmap.node.changed` does: the plugin reloads the tree. */
const serverEvent = (backend: ReturnType<typeof fakeMindmapBackend>) => backend.store.dispatch(mindmapApi.util.invalidateTags(["Tree"]) as never);
const shownIds = () => [...document.querySelectorAll("[data-flow-node]")].map((entry) => entry.getAttribute("data-flow-node"));
const flowNode = (id: string) => document.querySelector(`[data-flow-node='${id}']`) as HTMLElement;

describe("MindmapPage: showing the tree", () => {
	it("shows the marked project as the root and two levels of its tree, connected by edges", async () => {
		await renderPage();

		await screen.findByTestId(ids.node("a1"));
		expect(shownIds()).toEqual(["p1", "a", "a1", "b"]);
		expect(screen.getByTestId(ids.node("p1")).textContent).toContain("Viewer");
		expect(screen.getByTestId(ids.node("a")).textContent).toContain("Thema a");
		expect(document.querySelector("[data-flow-edge='a->a1']")).toBeTruthy();
		expect(Number(flowNode("a").dataset.x)).toBeGreaterThan(Number(flowNode("p1").dataset.x));
	});

	it("asks to choose a project when none is marked and several are visible", async () => {
		const backend = await renderPage({ documents: {} });

		expect((await screen.findByTestId(ids.chooseProject)).textContent).toContain("Projekt");
		expect(backend.calls("GET", "mindmap/trees")).toHaveLength(0);
	});

	it("shows the only visible project without a mark", async () => {
		await renderPage({ documents: { workspace: { hidden: ["p0"] } } });

		await screen.findByTestId(ids.node("a"));
		expect(shownIds()[0]).toBe("p1");
	});

	it("shows only the root of a project without nodes", async () => {
		await renderPage({ nodes: [] });

		await screen.findByTestId(ids.node("p1"));
		expect(shownIds()).toEqual(["p1"]);
	});
});

describe("MindmapPage: folding", () => {
	it("opens and closes a node and keeps the choice in the UI state of the server", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.node("a1"));

		fireEvent.click(screen.getByTestId(ids.toggle("a1")));
		await screen.findByTestId(ids.node("a11"));
		fireEvent.click(screen.getByTestId(ids.toggle("a")));
		await waitFor(() => expect(shownIds()).toEqual(["p1", "a", "b"]));

		const { flushUiState } = await import("../../../../../../client/src/core/ui-state/uiState");
		await waitFor(async () => {
			await flushUiState(backend.store);
			expect((backend.documents.get("mindmap") as { fold?: unknown }).fold).toEqual({ a1: "open", a: "closed" });
		});
	});

	it("starts with the stored fold state", async () => {
		await renderPage({ documents: { ...marked, mindmap: { fold: { a: "closed" } } } });

		await screen.findByTestId(ids.node("b"));
		expect(shownIds()).toEqual(["p1", "a", "b"]);
		expect(screen.queryByTestId(ids.toggle("b"))).toBeNull();
	});
});

describe("MindmapPage: creating and renaming", () => {
	it("adds a child, opens it for naming and saves the name on Enter", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.node("a1"));

		fireEvent.click(screen.getByTestId(ids.add("b")));
		const input = (await screen.findByTestId(ids.titleInput("new1"))) as HTMLInputElement;
		expect(backend.calls("POST", "mindmap/nodes")[0]!.body).toEqual({ project: "p1", title: "Neues Thema", parent: "b" });
		fireEvent.change(input, { target: { value: "Import" } });
		fireEvent.keyDown(input, { key: "Enter" });

		await waitFor(() => expect(screen.getByTestId(ids.node("new1")).textContent).toContain("Import"));
		expect(backend.calls("PUT", "mindmap/nodes/new1")[0]!.body).toEqual({ version: 1, title: "Import" });
		expect(screen.queryByTestId(ids.titleInput("new1"))).toBeNull();
	});

	it("adds a node under the root without a parent and opens a closed parent for the new child", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.node("a1"));

		fireEvent.click(screen.getByTestId(ids.add("p1")));
		await screen.findByTestId(ids.titleInput("new1"));
		expect(backend.calls("POST", "mindmap/nodes")[0]!.body).toEqual({ project: "p1", title: "Neues Thema" });

		fireEvent.click(screen.getByTestId(ids.add("a1")));
		await screen.findByTestId(ids.titleInput("new2"));
		expect(shownIds()).toContain("a11");
	});

	it("renames by double click; Esc leaves the title as it is", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.node("a"));

		fireEvent.doubleClick(screen.getByTestId(ids.node("a")));
		fireEvent.change(screen.getByTestId(ids.titleInput("a")), { target: { value: "Anders" } });
		fireEvent.keyDown(screen.getByTestId(ids.titleInput("a")), { key: "Escape" });
		expect(screen.queryByTestId(ids.titleInput("a"))).toBeNull();
		expect(backend.calls("PUT", "mindmap/nodes")).toHaveLength(0);

		fireEvent.doubleClick(screen.getByTestId(ids.node("a")));
		fireEvent.change(screen.getByTestId(ids.titleInput("a")), { target: { value: "Neu benannt" } });
		fireEvent.blur(screen.getByTestId(ids.titleInput("a")));
		await waitFor(() => expect(screen.getByTestId(ids.node("a")).textContent).toContain("Neu benannt"));
	});

	it("does not rename the root and offers it no trash", async () => {
		await renderPage();
		await screen.findByTestId(ids.node("p1"));

		fireEvent.doubleClick(screen.getByTestId(ids.node("p1")));

		expect(screen.queryByTestId(ids.titleInput("p1"))).toBeNull();
		expect(screen.queryByTestId(ids.remove("p1"))).toBeNull();
	});

	it("shows the message of the server above the map when a write fails", async () => {
		await renderPage({
			respond: ({ method, path }) =>
				method === "PUT" && path === "mindmap/nodes/a" ? Response.json({ code: "version_conflict", message: "Der Knoten wurde inzwischen geändert", details: {} }, { status: 409 }) : undefined,
		});
		await screen.findByTestId(ids.node("a"));

		fireEvent.doubleClick(screen.getByTestId(ids.node("a")));
		fireEvent.change(screen.getByTestId(ids.titleInput("a")), { target: { value: "X" } });
		fireEvent.keyDown(screen.getByTestId(ids.titleInput("a")), { key: "Enter" });

		expect((await screen.findByTestId(ids.error)).textContent).toContain("Der Knoten wurde inzwischen geändert");
	});
});

describe("MindmapPage: double click", () => {
	it("renames without opening the detail column", async () => {
		await renderPage();
		await screen.findByTestId(ids.node("a"));

		fireEvent.click(screen.getByTestId(ids.node("a")));
		fireEvent.click(screen.getByTestId(ids.node("a")));
		fireEvent.doubleClick(screen.getByTestId(ids.node("a")));

		await screen.findByTestId(ids.titleInput("a"));
		await new Promise((resolve) => setTimeout(resolve, 400));
		expect(screen.queryByTestId(ids.detail)).toBeNull();
	});
});

describe("MindmapPage: trash", () => {
	it("puts a node without children into the trash at once", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.node("b"));

		fireEvent.click(screen.getByTestId(ids.remove("b")));

		await waitFor(() => expect(backend.calls("DELETE", "workspace/elements/b")).toHaveLength(1));
		expect(backend.calls("DELETE", "workspace/elements/b")[0]!.query.get("version")).toBe("1");
		serverEvent(backend);
		await waitFor(() => expect(shownIds()).not.toContain("b"));
	});

	it("asks before a node with children goes to the trash with its branch", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.node("a"));

		fireEvent.click(screen.getByTestId(ids.remove("a")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.confirmDialogConfirm));

		await waitFor(() => expect(backend.calls("DELETE", "workspace/elements/a")).toHaveLength(2));
		expect(backend.calls("DELETE", "workspace/elements/a")[1]!.query.get("cascade")).toBe("true");
		serverEvent(backend);
		await waitFor(() => expect(shownIds()).toEqual(["p1", "b"]));
	});
});

describe("MindmapPage: detail column", () => {
	it("opens the clicked node with title and text, saves both and closes", async () => {
		const backend = await renderPage({ nodes: [node("a", null, 0, { text: "Alter Text" }), node("b", null, 1)] });
		await screen.findByTestId(ids.node("a"));
		expect(screen.queryByTestId(ids.detail)).toBeNull();

		fireEvent.click(flowNode("a"));
		const detail = await screen.findByTestId(ids.detail);
		expect(detail.textContent).toContain("NODE-a");
		const text = screen.getByTestId(sharedTestIds.inlineFieldInput("text")) as HTMLTextAreaElement;
		expect(text.value).toBe("Alter Text");

		fireEvent.change(text, { target: { value: "Neuer Text" } });
		fireEvent.blur(text);
		await waitFor(() => expect(backend.calls("PUT", "mindmap/nodes/a")[0]!.body).toEqual({ version: 1, text: "Neuer Text" }));

		const title = screen.getByTestId(sharedTestIds.inlineFieldInput("title")) as HTMLInputElement;
		fireEvent.change(title, { target: { value: "Titel neu" } });
		fireEvent.blur(title);
		await waitFor(() => expect(backend.calls("PUT", "mindmap/nodes/a")[1]!.body).toEqual({ version: 2, title: "Titel neu" }));
		await waitFor(() => expect(screen.getByTestId(ids.node("a")).textContent).toContain("Titel neu"));

		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("close")));
		await waitFor(() => expect(screen.queryByTestId(ids.detail)).toBeNull());
	});

	it("does not open a detail for the root and marks the selected node", async () => {
		await renderPage();
		await screen.findByTestId(ids.node("a"));

		fireEvent.click(flowNode("p1"));
		fireEvent.click(flowNode("b"));

		await screen.findByTestId(ids.detail);
		expect(screen.getByTestId(ids.node("b")).dataset.selected).toBe("true");
		expect(screen.getByTestId(ids.node("p1")).dataset.selected).toBe("false");
	});
});

/** Fires a drag event on a node whose box is 40 high: `offsetY` 2 is the upper quarter, 20 the middle, 38 the lower quarter. */
function dragEvent(type: "dragover" | "drop", target: HTMLElement, offsetY: number) {
	vi.spyOn(target, "getBoundingClientRect").mockReturnValue({ top: 0, height: 40, bottom: 40, left: 0, right: 100, width: 100, x: 0, y: 0, toJSON: () => ({}) });
	const dataTransfer = { setData: () => {}, getData: () => "", effectAllowed: "", dropEffect: "" };
	const event = Object.assign(new Event(type, { bubbles: true, cancelable: true }), { clientY: offsetY, dataTransfer });
	fireEvent(target, event);
	return event;
}
const startDrag = (id: string) => fireEvent.dragStart(screen.getByTestId(ids.node(id)), { dataTransfer: { setData: () => {}, effectAllowed: "" } });

describe("MindmapPage: moving by dragging", () => {
	it("hangs a node with its branch below the node it is dropped on", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.node("a1"));

		startDrag("a1");
		expect(dragEvent("dragover", screen.getByTestId(ids.node("b")), 20).defaultPrevented).toBe(true);
		expect(screen.getByTestId(ids.node("b")).dataset.drop).toBe("inside");
		dragEvent("drop", screen.getByTestId(ids.node("b")), 20);

		await waitFor(() => expect(shownIds()).toEqual(["p1", "a", "b", "a1"]));
		expect(backend.calls("POST", "mindmap/nodes/a1/move")[0]!.body).toEqual({ version: 1, parent: "b", position: 0 });
		expect(document.querySelector("[data-flow-edge='b->a1']")).toBeTruthy();
		expect(screen.getByTestId(ids.node("b")).dataset.drop).toBeUndefined();
	});

	it("changes the order of the siblings: the upper quarter places before, the lower quarter after the target", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.node("a1"));

		startDrag("b");
		dragEvent("dragover", screen.getByTestId(ids.node("a")), 2);
		expect(screen.getByTestId(ids.dropLine("a", "before"))).toBeTruthy();
		dragEvent("drop", screen.getByTestId(ids.node("a")), 2);
		await waitFor(() => expect(shownIds()).toEqual(["p1", "b", "a", "a1"]));
		expect(backend.calls("POST", "mindmap/nodes/b/move")[0]!.body).toEqual({ version: 1, parent: null, position: 0 });

		startDrag("b");
		dragEvent("dragover", screen.getByTestId(ids.node("a")), 38);
		expect(screen.getByTestId(ids.dropLine("a", "after"))).toBeTruthy();
		dragEvent("drop", screen.getByTestId(ids.node("a")), 38);
		await waitFor(() => expect(shownIds()).toEqual(["p1", "a", "a1", "b"]));
		expect(backend.calls("POST", "mindmap/nodes/b/move")[1]!.body).toEqual({ version: 2, parent: null, position: 1 });
	});

	it("hangs a node below the root with an empty parent", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.node("a1"));

		startDrag("a1");
		dragEvent("drop", screen.getByTestId(ids.node("p1")), 20);

		await waitFor(() => expect(shownIds()).toEqual(["p1", "a", "b", "a1", "a11"]));
		expect(backend.calls("POST", "mindmap/nodes/a1/move")[0]!.body).toEqual({ version: 1, parent: null, position: 2 });
	});

	it("opens a closed node when something is dropped on it", async () => {
		await renderPage();
		await screen.findByTestId(ids.node("a1"));
		expect(shownIds()).not.toContain("a11");

		startDrag("b");
		dragEvent("drop", screen.getByTestId(ids.node("a1")), 20);

		await waitFor(() => expect(shownIds()).toEqual(["p1", "a", "a1", "a11", "b"]));
	});

	it("does not offer what the structure forbids: the own branch, the node itself, a place next to the root", async () => {
		const backend = await renderPage();
		await screen.findByTestId(ids.node("a1"));

		startDrag("a");
		for (const [target, offset] of [["a1", 20], ["a", 20], ["p1", 2], ["b", 2]] as const) {
			const over = dragEvent("dragover", screen.getByTestId(ids.node(target)), offset);
			expect(over.defaultPrevented).toBe(false);
			expect(screen.getByTestId(ids.node(target)).dataset.drop).toBeUndefined();
			dragEvent("drop", screen.getByTestId(ids.node(target)), offset);
		}

		expect(backend.calls("POST", "/move")).toHaveLength(0);
		expect(screen.getByTestId(ids.node("p1")).getAttribute("draggable")).toBe("false");
		expect(screen.getByTestId(ids.node("a")).getAttribute("draggable")).toBe("true");
	});

	it("marks the dragged node and removes every mark when the drag ends or leaves", async () => {
		await renderPage();
		await screen.findByTestId(ids.node("a1"));

		startDrag("a1");
		dragEvent("dragover", screen.getByTestId(ids.node("b")), 20);
		fireEvent.dragLeave(screen.getByTestId(ids.node("b")));
		expect(screen.getByTestId(ids.node("b")).dataset.drop).toBeUndefined();
		dragEvent("dragover", screen.getByTestId(ids.node("b")), 20);
		fireEvent.dragEnd(screen.getByTestId(ids.node("a1")));

		expect(screen.getByTestId(ids.node("b")).dataset.drop).toBeUndefined();
		expect(dragEvent("dragover", screen.getByTestId(ids.node("b")), 20).defaultPrevented).toBe(false);
	});

	it("shows the message of the server above the map when it refuses the move, and leaves the tree as it is", async () => {
		await renderPage({
			respond: ({ method, path }) =>
				method === "POST" && path === "mindmap/nodes/a1/move" ? Response.json({ code: "mindmap_loop", message: "Ein Knoten kann nicht unter sich selbst hängen", details: {} }, { status: 400 }) : undefined,
		});
		await screen.findByTestId(ids.node("a1"));

		startDrag("a1");
		dragEvent("drop", screen.getByTestId(ids.node("b")), 20);

		expect((await screen.findByTestId(ids.error)).textContent).toContain("Ein Knoten kann nicht unter sich selbst hängen");
		expect(shownIds()).toEqual(["p1", "a", "a1", "b"]);
	});
});

describe("MindmapPage: notes at a node", () => {
	it("marks a node that has documents and no other", async () => {
		await renderPage({ nodes: [node("a", null, 0, { documents: ["NODE-a_notes.md"] }), node("b", null, 1)] });

		await screen.findByTestId(ids.node("a"));
		expect(screen.getByTestId(ids.notesMark("a"))).toBeTruthy();
		expect(screen.queryByTestId(ids.notesMark("b"))).toBeNull();
	});

	it("lists the documents of the node in its detail", async () => {
		await renderPage({ nodes: [node("a", null, 0, { documents: ["NODE-a_notes.md", "NODE-a_spec.md"] })] });
		await screen.findByTestId(ids.node("a"));

		fireEvent.click(flowNode("a"));

		await screen.findByTestId(ids.detail);
		expect(screen.getByTestId(sharedTestIds.document("NODE-a_notes.md"))).toBeTruthy();
		expect(screen.getByTestId(sharedTestIds.document("NODE-a_spec.md"))).toBeTruthy();
	});

	it("appends an entry to the notes and then marks the node in the map", async () => {
		const backend = await renderPage({ nodes: [node("a")] });
		await screen.findByTestId(ids.node("a"));
		expect(screen.queryByTestId(ids.notesMark("a"))).toBeNull();

		fireEvent.click(flowNode("a"));
		await screen.findByTestId(ids.detail);
		fireEvent.click(screen.getByTestId(sharedTestIds.documentsAddEntry));
		fireEvent.change(await screen.findByTestId(sharedTestIds.entryField("topic")), { target: { value: "Treffen" } });
		fireEvent.change(screen.getByTestId(sharedTestIds.entryField("discussed")), { target: { value: "a\n\nb" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.entrySave));

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a/entries")).toHaveLength(1));
		expect(backend.calls("POST", "mindmap/nodes/a/entries")[0]!.body).toEqual({ topic: "Treffen", discussed: ["a", "b"], decided: [], open: [] });
		await waitFor(() => expect(screen.getByTestId(ids.notesMark("a"))).toBeTruthy());
		expect(screen.getByTestId(sharedTestIds.document("NODE-a_notes.md"))).toBeTruthy();
	});

	it("creates a spec named after the label of the node", async () => {
		const backend = await renderPage({ nodes: [node("a")] });
		await screen.findByTestId(ids.node("a"));

		fireEvent.click(flowNode("a"));
		await screen.findByTestId(ids.detail);
		fireEvent.click(screen.getByTestId(sharedTestIds.documentsAddSpec));
		expect(((await screen.findByTestId(sharedTestIds.specName)) as HTMLInputElement).value).toBe("NODE-a_spec.md");
		fireEvent.click(screen.getByTestId(sharedTestIds.specSave));

		await waitFor(() => expect(backend.calls("PUT", "mindmap/nodes/a/documents/NODE-a_spec.md")).toHaveLength(1));
		expect(backend.calls("PUT", "mindmap/nodes/a/documents/NODE-a_spec.md")[0]!.body).toEqual({ content: "# NODE-a — Thema a\n" });
	});
});

describe("MindmapPage: count, ring and state", () => {
	const stated = [
		node("a", null, 0, { total: 4, done: 1, state: "in_progress" }),
		node("b", null, 1, { total: 2, done: 2, state: "done" }),
		node("c", null, 2),
		node("a1", "a", 0, { total: 1, done: 0, state: "planned" }),
	];

	it("shows count and progress ring at a node with items, nothing at a node without", async () => {
		await renderPage({ nodes: stated });

		const a = await screen.findByTestId(ids.node("a"));
		expect(screen.getByTestId(ids.count("a")).textContent).toBe("4");
		expect(a.querySelector(`[data-testid='${sharedTestIds.progressRing}']`)?.getAttribute("aria-label")).toBe("1/4");
		expect(screen.getByTestId(ids.count("b")).textContent).toBe("2");
		expect(screen.queryByTestId(ids.count("c"))).toBeNull();
		expect(screen.getByTestId(ids.node("c")).querySelector(`[data-testid='${sharedTestIds.progressRing}']`)).toBeNull();
	});

	it("draws an idea dashed and hollow and a finished node dimmed", async () => {
		await renderPage({ nodes: stated });

		await screen.findByTestId(ids.node("a"));
		expect(screen.getByTestId(ids.node("c")).dataset.state).toBe("idea");
		expect(getComputedStyle(screen.getByTestId(ids.node("c"))).borderStyle).toBe("dashed");
		expect(getComputedStyle(screen.getByTestId(ids.node("a"))).borderStyle).toBe("solid");
		expect(getComputedStyle(screen.getByTestId(ids.node("b"))).opacity).toBe("0.55");
		expect(getComputedStyle(screen.getByTestId(ids.node("a"))).opacity).toBe("1");
	});

	it("asks the server for the counts by the status filter of the backlog", async () => {
		const backend = await renderPage({ nodes: stated });
		await screen.findByTestId(ids.node("a"));

		expect(backend.calls("GET", "mindmap/trees")[0]!.query.get("statuses")).toBe("Open,In progress,Awaiting confirmation");
	});

	it("asks without a filter once the backlog lets every status pass", async () => {
		const backend = await renderPage({ nodes: stated, documents: { ...marked, backlog: { hiddenStatuses: [] } } });
		await screen.findByTestId(ids.node("a"));

		expect(backend.calls("GET", "mindmap/trees")[0]!.query.get("statuses")).toBeNull();
	});

	it("hides the nodes of a hidden state with their branch", async () => {
		await renderPage({ nodes: stated, documents: { ...marked, mindmap: { hiddenStates: ["in_progress", "idea"] } } });

		await screen.findByTestId(ids.node("b"));
		expect(shownIds()).toEqual(["p1", "b"]);
	});
});

describe("MindmapPage: the side view Nicht zugeordnet", () => {
	const loose = [itemRef("x1"), itemRef("x2", { status: "In progress" })];
	const startItemDrag = (uid: string) => fireEvent.dragStart(screen.getByTestId(ids.unassignedItem(uid)), { dataTransfer: { setData: () => {}, effectAllowed: "" } });

	it("lists the items without a node next to the map and keeps them out of the tree", async () => {
		await renderPage({ unassigned: loose });

		const panel = await screen.findByTestId(ids.unassigned);
		await screen.findByTestId(ids.unassignedItem("x1"));
		expect(panel.textContent).toContain("Nicht zugeordnet");
		expect(screen.getByTestId(ids.unassignedItem("x1")).textContent).toContain("TASK-x1");
		expect(screen.getByTestId(ids.unassignedItem("x2")).textContent).toContain("Aufgabe x2");
		await screen.findByTestId(ids.node("b"));
		expect(shownIds()).toEqual(["p1", "a", "a1", "b"]);
	});

	it("is not there while it is switched off", async () => {
		await renderPage({ unassigned: loose, documents: { ...marked, mindmap: { showUnassigned: false } } });

		await screen.findByTestId(ids.node("a"));
		expect(screen.queryByTestId(ids.unassigned)).toBeNull();
	});

	it("assigns an item to the node it is dropped on, and the item leaves the list", async () => {
		const backend = await renderPage({ unassigned: loose });
		await screen.findByTestId(ids.unassignedItem("x1"));
		await screen.findByTestId(ids.node("b"));

		startItemDrag("x1");
		expect(dragEvent("dragover", screen.getByTestId(ids.node("b")), 20).defaultPrevented).toBe(true);
		expect(screen.getByTestId(ids.node("b")).dataset.drop).toBe("inside");
		dragEvent("drop", screen.getByTestId(ids.node("b")), 20);

		await waitFor(() => expect(screen.queryByTestId(ids.unassignedItem("x1"))).toBeNull());
		expect(backend.calls("POST", "mindmap/nodes/b/items")[0]!.body).toEqual({ item: "x1" });
		expect(screen.getByTestId(ids.unassignedItem("x2"))).toBeTruthy();
		expect(screen.getByTestId(ids.node("b")).dataset.drop).toBeUndefined();
	});

	it("takes an item on any zone of a node as a drop on the node, never above or below it", async () => {
		const backend = await renderPage({ unassigned: loose });
		await screen.findByTestId(ids.unassignedItem("x1"));
		await screen.findByTestId(ids.node("b"));

		startItemDrag("x1");
		dragEvent("dragover", screen.getByTestId(ids.node("b")), 2);
		expect(screen.getByTestId(ids.node("b")).dataset.drop).toBe("inside");
		dragEvent("drop", screen.getByTestId(ids.node("b")), 2);

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/b/items")).toHaveLength(1));
	});

	it("offers no drop on the root (the project)", async () => {
		const backend = await renderPage({ unassigned: loose });
		await screen.findByTestId(ids.unassignedItem("x1"));
		await screen.findByTestId(ids.node("b"));

		startItemDrag("x1");
		expect(dragEvent("dragover", screen.getByTestId(ids.node("p1")), 20).defaultPrevented).toBe(false);
		dragEvent("drop", screen.getByTestId(ids.node("p1")), 20);

		expect(backend.calls("POST", "mindmap/nodes")).toHaveLength(0);
		expect(screen.getByTestId(ids.unassignedItem("x1"))).toBeTruthy();
	});

	it("shows the message of the server when the assignment is rejected", async () => {
		await renderPage({
			unassigned: loose,
			respond: ({ method, path }) =>
				method === "POST" && path === "mindmap/nodes/b/items" ? Response.json({ code: "mindmap_other_project", message: "Item und Knoten stehen in verschiedenen Projekten", details: {} }, { status: 400 }) : undefined,
		});
		await screen.findByTestId(ids.unassignedItem("x1"));
		await screen.findByTestId(ids.node("b"));

		startItemDrag("x1");
		dragEvent("dragover", screen.getByTestId(ids.node("b")), 20);
		dragEvent("drop", screen.getByTestId(ids.node("b")), 20);

		expect((await screen.findByTestId(ids.error)).textContent).toContain("verschiedenen Projekten");
		expect(screen.getByTestId(ids.unassignedItem("x1"))).toBeTruthy();
	});

	it("still moves nodes by dragging while the side view is on", async () => {
		const backend = await renderPage({ unassigned: loose });
		await screen.findByTestId(ids.node("a1"));

		startDrag("a1");
		dragEvent("dragover", screen.getByTestId(ids.node("b")), 20);
		dragEvent("drop", screen.getByTestId(ids.node("b")), 20);

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a1/move")).toHaveLength(1));
		expect(backend.calls("POST", "mindmap/nodes/b/items")).toHaveLength(0);
	});
});

describe("MindmapPage: marks", () => {
	const withMarks = [
		node("a", null, 0, { mark: "discarded", total: 2, done: 1, state: "in_progress" }),
		node("b", null, 1, { mark: "later" }),
		node("c", null, 2),
		node("a1", "a", 0, { total: 1, state: "planned" }),
	];

	it("sets a discarded node apart: symbol, struck-through title, dimmed; its count and state stay", async () => {
		await renderPage({ nodes: withMarks });

		await screen.findByTestId(ids.node("a"));
		const a = screen.getByTestId(ids.node("a"));
		expect(a.dataset.mark).toBe("discarded");
		expect(screen.getByTestId(ids.mark("a")).getAttribute("data-mark")).toBe("discarded");
		expect(getComputedStyle(a.querySelector("[class*='MuiTypography-body2']")!).textDecoration).toContain("line-through");
		expect(getComputedStyle(a).opacity).toBe("0.45");
		expect(a.dataset.state).toBe("in_progress");
		expect(screen.getByTestId(ids.count("a")).textContent).toBe("2");
	});

	it("marks a node for later with its own symbol and does not strike its title through", async () => {
		await renderPage({ nodes: withMarks });

		await screen.findByTestId(ids.node("b"));
		expect(screen.getByTestId(ids.node("b")).dataset.mark).toBe("later");
		expect(screen.getByTestId(ids.mark("b")).getAttribute("data-mark")).toBe("later");
		expect(getComputedStyle(screen.getByTestId(ids.node("b")).querySelector("[class*='MuiTypography-body2']")!).textDecoration).not.toContain("line-through");
	});

	it("shows nothing for a node without a mark, and nothing for the root", async () => {
		await renderPage({ nodes: withMarks });

		await screen.findByTestId(ids.node("c"));
		expect(screen.getByTestId(ids.node("c")).dataset.mark).toBeUndefined();
		expect(screen.queryByTestId(ids.mark("c"))).toBeNull();
		expect(screen.queryByTestId(ids.mark("p1"))).toBeNull();
	});

	it("hides the nodes of a hidden mark; the children of a hidden node go with it, but carry no mark", async () => {
		await renderPage({ nodes: withMarks, documents: { ...marked, mindmap: { hiddenMarks: ["discarded"] } } });

		await screen.findByTestId(ids.node("b"));
		expect(shownIds()).toEqual(["p1", "b", "c"]);
	});

	it("shows everything by default, marked nodes included", async () => {
		await renderPage({ nodes: withMarks });

		await screen.findByTestId(ids.node("b"));
		expect(shownIds()).toEqual(["p1", "a", "a1", "b", "c"]);
	});
});

describe("MindmapPage: focus", () => {
	it("shows only the branch from the focus in the address, with the path above the map", async () => {
		await renderPage({}, "/mindmap/main?focus=a");

		await screen.findByTestId(ids.node("a1"));
		expect(shownIds()).toEqual(["a", "a1", "a11"]);
		expect(document.querySelector("[data-flow-edge='p1->a']")).toBeNull();
		const path = screen.getByTestId(ids.path);
		expect(path.textContent).toContain("Viewer");
		expect(path.textContent).toContain("Thema a");
		expect(screen.getByTestId(ids.pathEntry("p1")).tagName).toBe("BUTTON");
		expect(screen.getByTestId(ids.pathEntry("a")).tagName).not.toBe("BUTTON");
	});

	it("counts the depth from the focus: two levels below it are open", async () => {
		await renderPage({}, "/mindmap/main?focus=a1");

		await screen.findByTestId(ids.node("a11"));
		expect(shownIds()).toEqual(["a1", "a11"]);
		expect([...screen.getByTestId(ids.path).querySelectorAll("[data-testid^='mindmap.path-entry.']")].map((entry) => entry.getAttribute("data-testid"))).toEqual([
			"mindmap.path-entry.p1",
			"mindmap.path-entry.a",
			"mindmap.path-entry.a1",
		]);
	});

	it("shows the whole tree and no path without a focus", async () => {
		await renderPage();

		await screen.findByTestId(ids.node("a1"));
		expect(shownIds()).toEqual(["p1", "a", "a1", "b"]);
		expect(screen.queryByTestId(ids.path)).toBeNull();
	});

	it("falls back to the project root for an unknown focus, the root itself or the focus of another tree", async () => {
		for (const address of ["/mindmap/main?focus=nowhere", "/mindmap/main?focus=p1", "/mindmap/main?focus="]) {
			cleanup();
			await renderPage({}, address);
			await screen.findByTestId(ids.node("a1"));

			expect(shownIds()).toEqual(["p1", "a", "a1", "b"]);
			expect(screen.queryByTestId(ids.path)).toBeNull();
		}
	});

	it("goes back to a node of the path with a click on its entry, to the whole map with a click on the project", async () => {
		await renderPage({}, "/mindmap/main?focus=a11");
		await screen.findByTestId(ids.pathEntry("a1"));

		fireEvent.click(screen.getByTestId(ids.pathEntry("a")));
		await waitFor(() => expect(location()).toBe("/mindmap/main?focus=a"));
		await waitFor(() => expect(shownIds()).toEqual(["a", "a1", "a11"]));

		fireEvent.click(screen.getByTestId(ids.pathEntry("p1")));
		await waitFor(() => expect(location()).toBe("/mindmap/main"));
		await waitFor(() => expect(shownIds()).toEqual(["p1", "a", "a1", "b"]));
		expect(screen.queryByTestId(ids.path)).toBeNull();
	});

	it("opens a node as the root of the view; the root of the project has no such action", async () => {
		await renderPage();
		await screen.findByTestId(ids.node("a1"));
		expect(screen.queryByTestId(ids.openAsRoot("p1"))).toBeNull();

		fireEvent.click(screen.getByTestId(ids.openAsRoot("a")));

		await waitFor(() => expect(location()).toBe("/mindmap/main?focus=a"));
		await waitFor(() => expect(shownIds()).toEqual(["a", "a1", "a11"]));
	});

	it("treats the focus node like any other node: it can be renamed and gets children", async () => {
		const backend = await renderPage({}, "/mindmap/main?focus=a");
		await screen.findByTestId(ids.node("a1"));

		fireEvent.doubleClick(screen.getByTestId(ids.node("a")));
		fireEvent.change(screen.getByTestId(ids.titleInput("a")), { target: { value: "Anders" } });
		fireEvent.keyDown(screen.getByTestId(ids.titleInput("a")), { key: "Enter" });
		await waitFor(() => expect(backend.calls("PUT", "mindmap/nodes/a")).toHaveLength(1));

		fireEvent.click(screen.getByTestId(ids.add("a")));
		await screen.findByTestId(ids.titleInput("new1"));
		expect(backend.calls("POST", "mindmap/nodes")[0]!.body).toEqual({ project: "p1", title: "Neues Thema", parent: "a" });
	});

	it("shows the whole tree when the focus node goes to the trash", async () => {
		const backend = await renderPage({}, "/mindmap/main?focus=a");
		await screen.findByTestId(ids.node("a1"));

		fireEvent.click(screen.getByTestId(ids.remove("a")));
		fireEvent.click(await screen.findByTestId(sharedTestIds.confirmDialogConfirm));
		await waitFor(() => expect(backend.calls("DELETE", "workspace/elements/a")).toHaveLength(2));
		serverEvent(backend);

		await waitFor(() => expect(shownIds()).toEqual(["p1", "b"]));
		expect(screen.queryByTestId(ids.path)).toBeNull();
	});
});

describe("MindmapPage: the arrangement of the map", () => {
	const edge = (id: string) => document.querySelector(`[data-flow-edge='${id}']`) as HTMLElement;
	const handles = (id: string) => [...flowNode(id).querySelectorAll("[data-handle]")].map((entry) => entry.getAttribute("data-handle")).sort();
	const x = (id: string) => Number(flowNode(id).getAttribute("data-x"));

	it("arranges the tree to the side at the start: every child right of its parent, edges from the right to the left side", async () => {
		await renderPage();
		await waitFor(() => expect(shownIds()).toContain("a1"));

		expect(x("a")).toBeGreaterThan(x("p1"));
		expect(x("a1")).toBeGreaterThan(x("a"));
		expect(edge("p1->a").getAttribute("data-source-handle")).toBe("right");
		expect(edge("p1->a").getAttribute("data-target-handle")).toBe("left");
		expect(edge("a->a1").getAttribute("data-source-handle")).toBe("right");
		expect(edge("a->a1").getAttribute("data-target-handle")).toBe("left");
	});

	it("arranges the map around the root when `layout` is `round`: the root in the middle, a branch on each side", async () => {
		await renderPage({ documents: { ...marked, mindmap: { layout: "round" } } });
		await waitFor(() => expect(shownIds()).toContain("a1"));

		expect(flowNode("p1").getAttribute("data-x")).toBe("-95");
		expect(flowNode("p1").getAttribute("data-y")).toBe("-18");
		expect(x("a")).toBeGreaterThan(x("p1"));
		expect(x("b")).toBeLessThan(x("p1"));
	});

	it("connects a child on the left of its parent from the left side to the right side", async () => {
		await renderPage({ documents: { ...marked, mindmap: { layout: "round" } } });
		await waitFor(() => expect(shownIds()).toContain("a1"));

		expect(edge("p1->a").getAttribute("data-source-handle")).toBe("right");
		expect(edge("p1->a").getAttribute("data-target-handle")).toBe("left");
		expect(edge("p1->b").getAttribute("data-source-handle")).toBe("left");
		expect(edge("p1->b").getAttribute("data-target-handle")).toBe("right");
	});

	it("gives the root a connection on every side to send edges from, and every other node on every side to take and send them", async () => {
		await renderPage();
		await waitFor(() => expect(shownIds()).toContain("a1"));

		expect(handles("p1")).toEqual(["source-bottom", "source-left", "source-right", "source-top"]);
		expect(handles("a")).toEqual(["source-bottom", "source-left", "source-right", "source-top", "target-bottom", "target-left", "target-right", "target-top"]);
	});

	it("connects a child straight below or above its parent from the bottom to the top, or the top to the bottom, in the round arrangement", async () => {
		// Three branches share the circle in thirds: the second one lies straight below the root, the third at the upper left.
		await renderPage({ nodes: [node("a"), node("b", null, 1), node("c", null, 2)], documents: { ...marked, mindmap: { layout: "round" } } });
		await waitFor(() => expect(shownIds()).toContain("c"));

		expect(edge("p1->b").getAttribute("data-source-handle")).toBe("bottom");
		expect(edge("p1->b").getAttribute("data-target-handle")).toBe("top");
		expect(edge("p1->a").getAttribute("data-source-handle")).toBe("right");
		expect(edge("p1->c").getAttribute("data-source-handle")).toBe("left");
	});

	it("uses only the left and right sides in the tree to the side, however far a child lies above or below", async () => {
		await renderPage({ nodes: [node("a"), node("b", null, 1), node("c", null, 2), node("d", null, 3), node("e", null, 4), node("f", null, 5), node("g", null, 6)] });
		await waitFor(() => expect(shownIds()).toContain("g"));

		for (const id of ["a", "b", "c", "d", "e", "f", "g"]) {
			expect(edge(`p1->${id}`).getAttribute("data-source-handle")).toBe("right");
			expect(edge(`p1->${id}`).getAttribute("data-target-handle")).toBe("left");
		}
	});

	it("rearranges the map when the arrangement is switched, and back", async () => {
		const backend = fakeMindmapBackend({ projects, nodes, documents: marked });
		await renderWorkspace(
			<>
				<LayoutSwitch />
				<MindmapPage />
			</>,
			{ backend, initialEntries: ["/mindmap/main"] },
		);
		await waitFor(() => expect(shownIds()).toContain("a1"));
		expect(x("b")).toBeGreaterThan(x("p1"));

		fireEvent.click(screen.getByTestId(ids.layoutOption("round")));
		await waitFor(() => expect(flowNode("p1").getAttribute("data-x")).toBe("-95"));
		expect(x("b")).toBeLessThan(x("p1"));

		fireEvent.click(screen.getByTestId(ids.layoutOption("side")));
		await waitFor(() => expect(x("b")).toBeGreaterThan(x("p1")));
	});
});

describe("MindmapPage: moving by dragging in the round arrangement", () => {
	const round = { documents: { ...marked, mindmap: { layout: "round" } } };

	it("keeps before and after on a branch right of the root", async () => {
		await renderPage({ ...round, nodes: [node("a"), node("b", null, 1)] });
		await screen.findByTestId(ids.node("b"));

		startDrag("b");
		dragEvent("dragover", screen.getByTestId(ids.node("a")), 2);

		expect(screen.getByTestId(ids.dropLine("a", "before"))).toBeTruthy();
	});

	it("turns before and after around on a branch left of the root, so the mark lies where the node lands", async () => {
		const backend = await renderPage({ ...round, nodes: [node("a"), node("b", null, 1)] });
		await screen.findByTestId(ids.node("b"));

		startDrag("a");
		dragEvent("dragover", screen.getByTestId(ids.node("b")), 2);
		expect(screen.getByTestId(ids.dropLine("b", "after"))).toBeTruthy();
		expect(screen.getByTestId(ids.dropLine("b", "after")).dataset.side).toBe("top");
		dragEvent("drop", screen.getByTestId(ids.node("b")), 2);

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a/move")).toHaveLength(1));
		expect(backend.calls("POST", "mindmap/nodes/a/move")[0]!.body).toEqual({ version: 1, parent: null, position: 1 });
	});

	it("offers only the inside on a branch straight below the root", async () => {
		await renderPage({ ...round, nodes: [node("a"), node("b", null, 1), node("c", null, 2)] });
		await screen.findByTestId(ids.node("c"));

		startDrag("c");
		dragEvent("dragover", screen.getByTestId(ids.node("b")), 2);

		expect(screen.getByTestId(ids.node("b")).dataset.drop).toBe("inside");
		expect(document.querySelector("[data-testid^='mindmap.drop-line.']")).toBeNull();
	});

	it("leaves the tree to the side as it is: the upper quarter still places before", async () => {
		await renderPage({ nodes: [node("a"), node("b", null, 1)] });
		await screen.findByTestId(ids.node("b"));

		startDrag("b");
		dragEvent("dragover", screen.getByTestId(ids.node("a")), 2);

		expect(screen.getByTestId(ids.dropLine("a", "before"))).toBeTruthy();
	});
});

describe("MindmapPage: the overall view", () => {
	const overall = { mindmap: { view: "all" } };
	const two = [
		node("a", null, 0, { total: 3, done: 1, state: "in_progress" }),
		node("a1", "a", 0, { total: 3, done: 1, state: "in_progress" }),
		node("b", null, 1),
		node("c", null, 0, { project_uid: "p0", total: 2, done: 2, state: "done" }),
	];
	const renderAll = (options: Parameters<typeof fakeMindmapBackend>[0] = {}) =>
		renderPage({ nodes: two, documents: { ...marked, ...overall }, ...options });

	it("shows a common root with the visible projects as its first nodes, each with its tree", async () => {
		await renderAll();

		await screen.findByTestId(ids.node("c"));
		expect(shownIds()).toEqual(["mindmap:all", "p0", "c", "p1", "a", "b"]);
		expect(screen.getByTestId(ids.node("mindmap:all")).textContent).toContain("Alle Projekte");
		expect(screen.getByTestId(ids.node("p1")).textContent).toContain("Viewer");
		expect(document.querySelector("[data-flow-edge='mindmap:all->p1']")).not.toBeNull();
		expect(document.querySelector("[data-flow-edge='p1->a']")).not.toBeNull();
	});

	it("counts every item once at the project nodes", async () => {
		await renderAll();

		await screen.findByTestId(ids.node("c"));
		expect(screen.getByTestId(ids.count("p1")).textContent).toBe("3");
		expect(screen.getByTestId(ids.count("p0")).textContent).toBe("2");
		expect(screen.getByTestId(ids.node("p0")).dataset.state).toBe("done");
		expect(screen.getByTestId(ids.node("p1")).dataset.state).toBe("in_progress");
	});

	it("shows only the projects switched on, at once when one is switched", async () => {
		await renderAll({ documents: { workspace: { marked: "p1", hidden: ["p0"] }, ...overall } });

		await screen.findByTestId(ids.node("a"));
		expect(shownIds()).toEqual(["mindmap:all", "p1", "a", "b"]);
	});

	it("offers nothing on the common root: no adding, and a project node can neither be removed nor renamed", async () => {
		await renderAll();
		await screen.findByTestId(ids.node("c"));

		expect(screen.queryByTestId(ids.add("mindmap:all"))).toBeNull();
		expect(screen.queryByTestId(ids.remove("mindmap:all"))).toBeNull();
		expect(screen.queryByTestId(ids.remove("p1"))).toBeNull();
		expect(screen.getByTestId(ids.add("p1"))).toBeTruthy();
		fireEvent.doubleClick(screen.getByTestId(ids.node("p1")));
		expect(screen.queryByTestId(ids.titleInput("p1"))).toBeNull();
	});

	it("adds a top node to the project of the node it is added at", async () => {
		const backend = await renderAll();
		await screen.findByTestId(ids.node("c"));

		fireEvent.click(screen.getByTestId(ids.add("p0")));

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes")).toHaveLength(1));
		expect(backend.calls("POST", "mindmap/nodes")[0]!.body).toMatchObject({ project: "p0" });
		expect(backend.calls("POST", "mindmap/nodes")[0]!.body).not.toHaveProperty("parent");
	});

	it("moves a node within its project only: a node of another project is not offered as a place", async () => {
		const backend = await renderAll();
		await screen.findByTestId(ids.node("c"));

		startDrag("a");
		dragEvent("dragover", screen.getByTestId(ids.node("c")), 20);
		expect(screen.getByTestId(ids.node("c")).dataset.drop).toBeUndefined();
		dragEvent("dragover", screen.getByTestId(ids.node("p1")), 20);
		expect(screen.getByTestId(ids.node("p1")).dataset.drop).toBe("inside");
		dragEvent("drop", screen.getByTestId(ids.node("p1")), 20);

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a/move")).toHaveLength(1));
		expect(backend.calls("POST", "mindmap/nodes/a/move")[0]!.body).toMatchObject({ parent: null });
	});

	it("shows the items without a node of the marked project, else the side view is off", async () => {
		await renderAll({ unassigned: [itemRef("x1")] });
		await screen.findByTestId(ids.unassignedItem("x1"));
		cleanup();

		await renderAll({ unassigned: [itemRef("x1")], documents: { ...overall } });
		await screen.findByTestId(ids.node("c"));
		expect(screen.queryByTestId(ids.unassigned)).toBeNull();
	});

	it("starts at a project when the address has its uid as the focus, with the path back to the common root", async () => {
		await renderPage({ nodes: two, documents: { ...marked, ...overall } }, "/mindmap/main?focus=p1");

		await screen.findByTestId(ids.pathEntry("p1"));
		await waitFor(() => expect(shownIds()).toEqual(["p1", "a", "a1", "b"]));
		expect(screen.getByTestId(ids.pathEntry("mindmap:all")).textContent).toBe("Alle Projekte");
	});

	it("asks to choose a project when none is visible", async () => {
		await renderAll({ documents: { workspace: { hidden: ["p0", "p1"] }, ...overall } });

		await screen.findByTestId(ids.chooseProject);
		expect(screen.getByTestId(ids.chooseProject).textContent).toContain("Gesamtansicht");
	});
});
