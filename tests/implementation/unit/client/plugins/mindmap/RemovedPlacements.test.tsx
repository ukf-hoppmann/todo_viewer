import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { NodeDetail } from "../../../../../../client/src/plugins/mindmap/NodeDetail";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { node } from "../../../../../helpers/client/mindmapFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const entry = (over: Record<string, unknown> = {}) => ({ tree_uid: "m1", kind: "free", name: "Ideen", parent_uid: "p", parent_available: true, nodes: 3, ...over });

async function renderDetail(removed: unknown[], restored: Record<string, unknown> = { node_uid: "a", tree_uid: "m1", nodes_restored: 3, nodes_skipped: 0, parent_uid: "p", fell_back_to_root: false }) {
	const shown = node("a", null, 0, { version: 5 });
	const backend = fakeMindmapBackend({
		projects: [project("p1", "Viewer", 1)],
		nodes: [shown],
		respond: ({ method, path }) => {
			if (method === "GET" && path === "mindmap/nodes/a/removed") return Response.json(removed);
			if (method === "POST" && path === "mindmap/nodes/a/restore-placement") return Response.json(restored);
			return undefined;
		},
	});
	await renderWorkspace(<NodeDetail node={shown} onClose={() => {}} />, { backend });
	return backend;
}

describe("NodeDetail: Früher in …", () => {
	it("shows nothing when no placement is remembered", async () => {
		await renderDetail([]);

		expect(screen.queryByTestId(ids.removedSection)).toBeNull();
	});

	it("lists the trees the branch was removed from and says when the old parent is gone", async () => {
		await renderDetail([entry(), entry({ tree_uid: "m2", name: "Mehr", parent_available: false })]);

		expect(await screen.findByTestId(ids.removedEntry("m1"))).toHaveProperty("textContent", expect.stringContaining("Ideen (3 Knoten)"));
		expect(screen.getByTestId(ids.removedEntry("m2")).textContent).toContain("unter die Wurzel");
		expect(screen.getByTestId(ids.removedEntry("m1")).textContent).not.toContain("unter die Wurzel");
	});

	it("puts the branch back with the version of the node and the tree", async () => {
		const backend = await renderDetail([entry()]);

		fireEvent.click(await screen.findByTestId(ids.removedRestore("m1")));

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a/restore-placement")).toHaveLength(1));
		expect(backend.calls("POST", "mindmap/nodes/a/restore-placement")[0]!.body).toEqual({ version: 5, tree: "m1" });
		expect((await screen.findByTestId(ids.removedNotice)).textContent).toContain("Wieder eingesetzt in Ideen");
	});

	it("tells when the branch came back under the root", async () => {
		await renderDetail([entry({ parent_available: false })], { node_uid: "a", tree_uid: "m1", nodes_restored: 1, nodes_skipped: 0, parent_uid: null, fell_back_to_root: true });

		fireEvent.click(await screen.findByTestId(ids.removedRestore("m1")));

		expect((await screen.findByTestId(ids.removedNotice)).textContent).toContain("unter der Wurzel");
	});

	it("shows the message of the server when restoring is refused", async () => {
		const backend = fakeMindmapBackend({
			projects: [project("p1", "Viewer", 1)],
			nodes: [node("a")],
			respond: ({ method, path }) => {
				if (method === "GET" && path === "mindmap/nodes/a/removed") return Response.json([entry()]);
				if (method === "POST") return Response.json({ code: "mindmap_node_in_tree", message: "Der Knoten steht in diesem Baum schon wieder", details: {} }, { status: 400 });
				return undefined;
			},
		});
		await renderWorkspace(<NodeDetail node={node("a")} onClose={() => {}} />, { backend });

		fireEvent.click(await screen.findByTestId(ids.removedRestore("m1")));

		expect((await screen.findByTestId(ids.removedNotice)).textContent).toContain("steht in diesem Baum schon wieder");
	});
});
