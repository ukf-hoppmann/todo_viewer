import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { backlogTestIds as ids } from "../../../../../../client/src/plugins/backlog/testIds";
import { detail, item } from "../../../../../helpers/client/backlogFixtures";
import { fakeWorkspaceBackend, project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

// jsdom has no layout: React Flow is replaced by a list of the nodes it is given and a record of its edges.
vi.mock("@xyflow/react", () => {
	const Handle = () => null;
	return {
		Handle,
		Position: { Left: "left", Right: "right" },
		MarkerType: { ArrowClosed: "arrowclosed" },
		Background: () => null,
		Controls: () => null,
		ReactFlow: (props: {
			nodes: Array<{ id: string; type: string; data: unknown }>;
			edges: Array<{ id: string; data?: { active: boolean }; style?: { strokeOpacity?: number } }>;
			nodeTypes: Record<string, (props: { data: unknown }) => ReactNode>;
			onNodeClick: (event: unknown, node: { id: string }) => void;
			onPaneClick: () => void;
			onNodeMouseEnter: (event: unknown, node: { id: string }) => void;
			onNodeMouseLeave: () => void;
		}) => (
			<div data-testid="flow" onClick={props.onPaneClick}>
				{props.nodes.map((node) => {
					const Node = props.nodeTypes[node.type]!;
					return (
						<div
							key={node.id}
							data-flow-node={node.id}
							onClick={(event) => {
								event.stopPropagation();
								props.onNodeClick(event, node);
							}}
							onMouseEnter={(event) => props.onNodeMouseEnter(event, node)}
							onMouseLeave={props.onNodeMouseLeave}
						>
							<Node data={node.data} />
						</div>
					);
				})}
				{props.edges.map((edge) => (
					<span key={edge.id} data-testid={ids.graphEdge(edge.id)} data-active={String(edge.data?.active)} data-opacity={edge.style?.strokeOpacity} />
				))}
			</div>
		),
	};
});
vi.mock("@xyflow/react/dist/style.css", () => ({}));

const { default: GraphPage } = await import("../../../../../../client/src/plugins/backlog/pages/GraphPage");

afterEach(cleanup);

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const items = [
	item("a", { project_uid: "p1", progress: { done: 1, total: 2 } }),
	item("b", { project_uid: "p1", dependencies: ["a"], priority: "Urgent", status: "In progress" }),
	item("c", { project_uid: "p1", dependencies: ["b"] }),
	item("x", { project_uid: "p1" }),
	item("y", { project_uid: "p1", dependencies: ["x"] }),
	item("lonely", { project_uid: "p1" }),
	item("done", { project_uid: "p1", status: "Completed", dependencies: ["a"] }),
];

async function renderGraph(options: Parameters<typeof fakeWorkspaceBackend>[0] = {}) {
	const backend = fakeWorkspaceBackend({ projects, backlog: items, details: { b: detail("b", { title: "Titel b" }) }, ...options });
	await renderWorkspace(<GraphPage />, { backend });
	await screen.findByTestId(ids.graphNode("a"));
	return backend;
}
const node = (uid: string) => screen.getByTestId(ids.graphNode(uid));
const flowNode = (uid: string) => document.querySelector(`[data-flow-node='${uid}']`) as HTMLElement;

describe("GraphPage", () => {
	it("shows only items with a dependency, with label, title and progress, and says how many", async () => {
		await renderGraph();

		expect(["a", "b", "c", "x", "y"].every((uid) => document.querySelector(`[data-flow-node='${uid}']`))).toBe(true);
		expect(document.querySelector("[data-flow-node='lonely']")).toBeNull();
		expect(node("a").textContent).toContain("A");
		expect(node("a").textContent).toContain("Titel a");
		expect(screen.getByTestId(ids.graphInfo).textContent).toBe("5 von 6 Items haben Abhängigkeiten");
		expect(screen.getByTestId(ids.graphEdge("a->b"))).toBeTruthy();
	});

	it("hides finished items like the tree does until the filter is switched", async () => {
		await renderGraph();
		expect(document.querySelector("[data-flow-node='done']")).toBeNull();
		cleanup();

		await renderGraph({ documents: { backlog: { hiddenStatuses: [] } } });
		await waitFor(() => expect(document.querySelector("[data-flow-node='done']")).not.toBeNull());
	});

	it("says so when no item has a dependency", async () => {
		const backend = fakeWorkspaceBackend({ projects, backlog: [item("a", { project_uid: "p1" })] });
		await renderWorkspace(<GraphPage />, { backend });

		expect((await screen.findByTestId(ids.graphEmpty)).textContent).toContain("Keine Items mit Abhängigkeiten");
	});

	it("selects a node on click, highlights it with its edges and neighbors and dims the rest, and shows its details", async () => {
		await renderGraph();

		fireEvent.click(flowNode("b"));

		await waitFor(() => expect(node("b").getAttribute("data-selected")).toBe("true"));
		expect(node("a").getAttribute("data-dimmed")).toBe("false");
		expect(node("c").getAttribute("data-dimmed")).toBe("false");
		expect(node("x").getAttribute("data-dimmed")).toBe("true");
		expect(screen.getByTestId(ids.graphEdge("a->b")).getAttribute("data-active")).toBe("true");
		expect(screen.getByTestId(ids.graphEdge("x->y")).getAttribute("data-active")).toBe("false");
		expect(screen.getByTestId(ids.graphEdge("x->y")).getAttribute("data-opacity")).toBe("0.12");
		expect((await screen.findByTestId(ids.detail)).textContent).toContain("Titel b");
	});

	it("highlights the hovered node while the pointer is on it", async () => {
		await renderGraph();

		fireEvent.mouseEnter(flowNode("x"));
		await waitFor(() => expect(node("a").getAttribute("data-dimmed")).toBe("true"));
		expect(node("y").getAttribute("data-dimmed")).toBe("false");
		fireEvent.mouseLeave(flowNode("x"));

		await waitFor(() => expect(node("a").getAttribute("data-dimmed")).toBe("false"));
	});

	it("marks more nodes with a modifier click and toggles them off again", async () => {
		await renderGraph();

		fireEvent.click(flowNode("a"));
		fireEvent.click(flowNode("x"), { ctrlKey: true });
		await waitFor(() => expect(node("x").getAttribute("data-selected")).toBe("true"));
		await waitFor(() => expect(node("a").getAttribute("data-selected")).toBe("true"));
		expect(node("y").getAttribute("data-dimmed")).toBe("false");
		expect(node("b").getAttribute("data-dimmed")).toBe("false");

		fireEvent.click(flowNode("x"), { shiftKey: true });
		await waitFor(() => expect(node("x").getAttribute("data-selected")).toBe("false"));
	});

	it("deselects with a second click, with the background and with Esc, which also clears the marks", async () => {
		await renderGraph();
		fireEvent.click(flowNode("b"));
		await waitFor(() => expect(node("b").getAttribute("data-selected")).toBe("true"));

		fireEvent.click(flowNode("b"));
		await waitFor(() => expect(node("b").getAttribute("data-selected")).toBe("false"));

		fireEvent.click(flowNode("a"));
		fireEvent.click(flowNode("x"), { metaKey: true });
		await waitFor(() => expect(node("x").getAttribute("data-selected")).toBe("true"));
		fireEvent.keyDown(window, { key: "Escape" });
		await waitFor(() => expect(node("x").getAttribute("data-selected")).toBe("false"));
		await waitFor(() => expect(node("a").getAttribute("data-selected")).toBe("false"));
		expect(node("c").getAttribute("data-dimmed")).toBe("false");

		fireEvent.click(flowNode("b"));
		await waitFor(() => expect(node("b").getAttribute("data-selected")).toBe("true"));
		fireEvent.click(screen.getByTestId("flow"));
		await waitFor(() => expect(node("b").getAttribute("data-selected")).toBe("false"));
	});
});
