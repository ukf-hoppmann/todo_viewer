import { cleanup, createEvent, fireEvent, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushUiState } from "../../../../../../client/src/core/ui-state/uiState";
import { MapFilters } from "../../../../../../client/src/plugins/mindmap/MapFilters";
import { MapList } from "../../../../../../client/src/plugins/mindmap/MapList";
import { NODE_MIME } from "../../../../../../client/src/plugins/mindmap/domain/branches";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { node } from "../../../../../helpers/client/mindmapFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

// jsdom has no layout: React Flow is replaced by a list of the nodes it is given.
vi.mock("@xyflow/react", () => {
	const Handle = () => <span />;
	return {
		Handle,
		MarkerType: { ArrowClosed: "arrowclosed" },
		Position: { Left: "left", Right: "right" },
		Background: () => null,
		Controls: () => null,
		ReactFlow: (props: { nodes: Array<{ id: string; type: string; data: unknown }>; nodeTypes: Record<string, (props: { data: unknown }) => ReactNode> }) => (
			<div>
				{props.nodes.map((entry) => {
					const Node = props.nodeTypes[entry.type]!;
					return (
						<div key={entry.id} data-flow-node={entry.id}>
							<Node data={entry.data} />
						</div>
					);
				})}
			</div>
		),
	};
});
vi.mock("@xyflow/react/dist/style.css", () => ({}));

const { default: MindmapPage } = await import("../../../../../../client/src/plugins/mindmap/pages/MindmapPage");

afterEach(cleanup);

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const marked = { workspace: { marked: "p1" } };
const maps = [{ uid: "f1", project_uid: "p1", name: "Ideen" }];
// a (a1) and b in the project tree; "Thema a1" also stands in the free map f1, so f1 cannot take the branch of a.
const nodes = [node("a"), node("a1", "a"), node("b", null, 1), node("a1", null, 0, { tree_uid: "f1" })];
const ok = () => Response.json(node("a"));

async function renderPage(options: Parameters<typeof fakeMindmapBackend>[0] = {}) {
	const backend = fakeMindmapBackend({ projects, nodes, maps, documents: marked, respond: ({ method, path }) => (method === "POST" && /\/(move-to-map|transfer|remove)$/.test(path) ? ok() : undefined), ...options });
	await renderWorkspace(<MindmapPage />, { backend });
	return backend;
}
const rightClick = (id: string) => fireEvent.contextMenu(screen.getByTestId(ids.node(id)));

describe("the menu of a node", () => {
	it("offers hanging over and transferring, and only for a node in one tree: delete", async () => {
		await renderPage();
		await screen.findByTestId(ids.node("b"));

		rightClick("b");

		expect(await screen.findByTestId(ids.nodeMenuMove)).toBeTruthy();
		expect(screen.getByTestId(ids.nodeMenuTransfer)).toBeTruthy();
		expect(screen.getByTestId(ids.nodeMenuTransferBranch).textContent).toBe("Ast überführen …");
		expect(screen.getByTestId(ids.nodeMenuDelete).textContent).toBe("Löschen");
		expect(screen.queryByTestId(ids.nodeMenuRemoveHere)).toBeNull();
	});

	it("offers \"Hier entfernen\" and \"Knoten löschen\" for a node in several trees and removes without a question", async () => {
		const backend = await renderPage({ nodes: [node("a", null, 0, { tree_count: 2 }), node("b", null, 1)] });
		await screen.findByTestId(ids.node("a"));

		rightClick("a");
		expect(screen.getByTestId(ids.nodeMenuDelete).textContent).toBe("Knoten löschen …");
		fireEvent.click(await screen.findByTestId(ids.nodeMenuRemoveHere));

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a/remove")).toHaveLength(1));
		expect(backend.calls("POST", "mindmap/nodes/a/remove")[0]!.body).toEqual({ version: 1, tree: "t1" });
		expect(screen.queryByTestId(sharedTestIds.confirmDialogConfirm)).toBeNull();
	});

	it("asks with the trees before a node in several trees is deleted everywhere", async () => {
		const backend = await renderPage({
			nodes: [node("a", null, 0, { tree_count: 2 })],
			respond: ({ method, path }) => {
				if (method === "GET" && path === "mindmap/nodes/a/trees") return Response.json([{ tree_uid: "t1", kind: "project", name: "Viewer", parent_uid: null }, { tree_uid: "f1", kind: "free", name: "Ideen", parent_uid: null }]);
				if (method === "DELETE" && path === "mindmap/nodes/a") return Response.json({ node_uid: "a", nodes_deleted: 1, kept_elsewhere: 0 });
				return undefined;
			},
		});
		await screen.findByTestId(ids.node("a"));

		fireEvent.click(screen.getByTestId(ids.remove("a")));

		await waitFor(() => expect(document.body.textContent).toContain("Viewer (Projektbaum), Ideen"));
		expect(backend.calls("DELETE", "mindmap/nodes/a")).toHaveLength(0);
		fireEvent.click(screen.getByTestId(sharedTestIds.confirmDialogConfirm));
		await waitFor(() => expect(backend.calls("DELETE", "mindmap/nodes/a")).toHaveLength(1));
		expect(backend.calls("DELETE", "mindmap/nodes/a")[0]!.query.get("version")).toBe("1");
		expect(backend.calls("DELETE", "workspace/elements/a")).toHaveLength(0);
	});
});

describe("hanging over and transferring in the dialog", () => {
	it("hangs a branch over to the chosen map", async () => {
		const backend = await renderPage({ nodes: [node("a"), node("a1", "a"), node("b", null, 1)], maps: [{ uid: "f1", project_uid: "p1", name: "Ideen" }] });
		await screen.findByTestId(ids.node("a"));
		rightClick("a");
		fireEvent.click(await screen.findByTestId(ids.nodeMenuMove));

		await screen.findByTestId(ids.branchDialog);
		fireEvent.click(await screen.findByTestId(ids.branchTarget("f1")));
		fireEvent.click(screen.getByTestId(ids.branchConfirm));

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a/move-to-map")).toHaveLength(1));
		expect(backend.calls("POST", "mindmap/nodes/a/move-to-map")[0]!.body).toEqual({ version: 1, target: "f1", tree: "t1" });
		await waitFor(() => expect(screen.queryByTestId(ids.branchDialog)).toBeNull());
	});

	it("opens the dialog \"Ast überführen\" with the branch of the node", async () => {
		await renderPage({ nodes: [node("a"), node("a1", "a"), node("b", null, 1)] });
		await screen.findByTestId(ids.node("a"));
		rightClick("a");
		fireEvent.click(await screen.findByTestId(ids.nodeMenuTransferBranch));

		await screen.findByTestId(ids.transferDialog);
		await screen.findByTestId(ids.transferRow("a1"));
		expect(screen.getByTestId(ids.transferRow("a"))).toBeTruthy();
		expect(screen.queryByTestId(ids.transferRow("b"))).toBeNull();
	});

	it("transfers a branch when asked to", async () => {
		const backend = await renderPage({ nodes: [node("a"), node("b", null, 1)] });
		await screen.findByTestId(ids.node("a"));
		rightClick("a");
		fireEvent.click(await screen.findByTestId(ids.nodeMenuTransfer));

		fireEvent.click(await screen.findByTestId(ids.branchTarget("f1")));
		fireEvent.click(screen.getByTestId(ids.branchConfirm));

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a/transfer")).toHaveLength(1));
		expect(backend.calls("POST", "mindmap/nodes/a/transfer")[0]!.body).toEqual({ version: 1, target: "f1", tree: "t1" });
	});

	it("greys out a target that holds part of the branch, with the nodes as the reason, and the own tree for a transfer", async () => {
		await renderPage();
		await screen.findByTestId(ids.node("a"));
		rightClick("a");
		fireEvent.click(await screen.findByTestId(ids.nodeMenuTransfer));

		await waitFor(() => expect(screen.getByTestId(ids.branchReason("f1")).textContent).toBe("Dort steht schon: Thema a1"));
		expect(screen.getByTestId(ids.branchReason("t1")).textContent).toBe("Hier steht der Ast schon.");
		expect((screen.getByTestId(ids.branchTarget("f1")) as HTMLInputElement).disabled).toBe(true);
		expect((screen.getByTestId(ids.branchTarget("t1")) as HTMLInputElement).disabled).toBe(true);
		expect((screen.getByTestId(ids.branchConfirm) as HTMLButtonElement).disabled).toBe(true);
	});

	it("shows the message and the nodes the server names when it refuses", async () => {
		await renderPage({
			nodes: [node("a"), node("a1", "a")],
			respond: ({ method, path }) =>
				method === "POST" && path.endsWith("/move-to-map")
					? Response.json({ code: "mindmap_target_conflict", message: "Der Ast oder ein Unterknoten steht im Ziel schon", details: { nodes: ["a1"] } }, { status: 400 })
					: undefined,
		});
		await screen.findByTestId(ids.node("a"));
		rightClick("a");
		fireEvent.click(await screen.findByTestId(ids.nodeMenuMove));
		fireEvent.click(await screen.findByTestId(ids.branchTarget("f1")));
		fireEvent.click(screen.getByTestId(ids.branchConfirm));

		await waitFor(() => expect(screen.getByTestId(ids.branchError).textContent).toBe("Der Ast oder ein Unterknoten steht im Ziel schon: Thema a1"));
		expect(screen.getByTestId(ids.branchDialog)).toBeTruthy();
	});
});

describe("transferred branches", () => {
	it("shows the number of trees at a shared node on hover and lists the trees to jump to", async () => {
		const backend = await renderPage({
			nodes: [node("a", null, 0, { tree_count: 3 }), node("b", null, 1)],
			respond: ({ method, path }) => (method === "GET" && path === "mindmap/nodes/a/trees" ? Response.json([{ tree_uid: "t1", kind: "project", name: "Viewer", parent_uid: null }, { tree_uid: "f1", kind: "free", name: "Ideen", parent_uid: null }]) : undefined),
		});
		await screen.findByTestId(ids.node("a"));
		expect(screen.queryByTestId(ids.sharedBadge("b"))).toBeNull();
		expect(screen.getByTestId(ids.sharedBadge("a")).textContent).toBe("3");

		fireEvent.click(screen.getByTestId(ids.sharedBadge("a")));
		fireEvent.click(await screen.findByTestId(ids.treeJump("f1")));

		await waitFor(() => expect(screen.queryByTestId(ids.treeJumpMenu)).toBeNull());
		await flushUiState(backend.store);
		expect((backend.documents.get("mindmap") as { maps?: Record<string, string> }).maps).toEqual({ p1: "f1" });
	});

	it("frames the shared nodes only while the switch is on", async () => {
		const backend = fakeMindmapBackend({ projects, nodes: [node("a", null, 0, { tree_count: 2 })], documents: marked });
		await renderWorkspace(
			<>
				<MapFilters />
				<MindmapPage />
			</>,
			{ backend },
		);
		await screen.findByTestId(ids.node("a"));
		const border = () => getComputedStyle(screen.getByTestId(ids.node("a"))).borderColor;
		const before = border();

		fireEvent.click(screen.getByTestId(ids.sharedSwitch));

		await waitFor(() => expect(border()).not.toBe(before));
		fireEvent.click(screen.getByTestId(ids.sharedSwitch));
		await waitFor(() => expect(border()).toBe(before));
	});
});

describe("dragging a node onto the map list", () => {
	it("asks whether to hang over or transfer when a node is dropped on a map", async () => {
		const backend = fakeMindmapBackend({ projects, nodes: [node("a")], maps, documents: marked });
		await renderWorkspace(<MapList />, { backend });
		const entry = await screen.findByTestId(ids.mapEntry("f1"));
		const carried = JSON.stringify({ uid: "a", version: 1, title: "Thema a", project_uid: "p1", tree_uid: "t1" });
		const data = { types: [NODE_MIME], getData: (type: string) => (type === NODE_MIME ? carried : "") };

		const over = createEvent.dragOver(entry);
		Object.defineProperty(over, "dataTransfer", { value: data });
		fireEvent(entry, over);
		expect(over.defaultPrevented).toBe(true);
		const drop = createEvent.drop(entry);
		Object.defineProperty(drop, "dataTransfer", { value: data });
		fireEvent(entry, drop);

		const dialog = await screen.findByTestId(ids.branchDialog);
		expect(dialog.textContent).toContain("Thema a");
		expect((screen.getByTestId(ids.branchTarget("f1")) as HTMLInputElement).checked).toBe(true);
		fireEvent.click(screen.getByTestId(ids.branchAction("transfer")));
		fireEvent.click(screen.getByTestId(ids.branchConfirm));
		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a/transfer")).toHaveLength(1));
		expect(backend.calls("POST", "mindmap/nodes/a/transfer")[0]!.body).toEqual({ version: 1, target: "f1", tree: "t1" });
	});

	it("ignores a drag that carries no node", async () => {
		const backend = fakeMindmapBackend({ projects, nodes: [node("a")], maps, documents: marked });
		await renderWorkspace(<MapList />, { backend });
		const entry = await screen.findByTestId(ids.mapEntry("f1"));
		const over = createEvent.dragOver(entry);
		Object.defineProperty(over, "dataTransfer", { value: { types: ["text/plain"], getData: () => "" } });
		fireEvent(entry, over);
		expect(over.defaultPrevented).toBe(false);
	});
});
