import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { NodeDetail } from "../../../../../../client/src/plugins/mindmap/NodeDetail";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { node } from "../../../../../helpers/client/mindmapFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

async function renderDetail(shown = node("a"), options: Parameters<typeof fakeMindmapBackend>[0] = {}) {
	const backend = fakeMindmapBackend({ projects: [project("p1", "Viewer", 1)], nodes: [shown], ...options });
	await renderWorkspace(<NodeDetail node={shown} onClose={() => {}} />, { backend });
	return backend;
}
const field = () => screen.getByTestId(sharedTestIds.inlineFieldInput("mark"));
const choose = (value: string) => {
	fireEvent.mouseDown(field());
	fireEvent.click(screen.getByTestId(`${sharedTestIds.inlineFieldInput("mark")}.${value}`));
};

describe("NodeDetail: the mark of a node", () => {
	it("shows no mark for a node without one", async () => {
		await renderDetail();

		expect(field().textContent).toBe("Keine");
	});

	it("shows the mark a node carries", async () => {
		await renderDetail(node("a", null, 0, { mark: "later" }));

		expect(field().textContent).toBe("Später");
	});

	it("sets a mark with the version of the node", async () => {
		const backend = await renderDetail(node("a", null, 0, { version: 4 }));

		choose("discarded");

		await waitFor(() => expect(backend.calls("PUT", "mindmap/nodes/a")).toHaveLength(1));
		expect(backend.calls("PUT", "mindmap/nodes/a")[0]!.body).toEqual({ version: 4, mark: "discarded" });
	});

	it("clears the mark with an empty value", async () => {
		const backend = await renderDetail(node("a", null, 0, { mark: "later" }));

		choose("none");

		await waitFor(() => expect(backend.calls("PUT", "mindmap/nodes/a")).toHaveLength(1));
		expect(backend.calls("PUT", "mindmap/nodes/a")[0]!.body).toEqual({ version: 1, mark: "" });
	});

	it("shows the message of the server at the field when the mark is refused", async () => {
		await renderDetail(node("a"), {
			respond: ({ method, path }) => (method === "PUT" && path === "mindmap/nodes/a" ? Response.json({ code: "mindmap_node_deleted", message: "Der Knoten liegt im Papierkorb", details: {} }, { status: 400 }) : undefined),
		});

		choose("later");

		expect((await screen.findByTestId(sharedTestIds.inlineFieldError("mark"))).textContent).toContain("Papierkorb");
	});

	it("does not touch title or text when only the mark changes", async () => {
		const backend = await renderDetail(node("a", null, 0, { title: "Alt", text: "Text" }));

		choose("later");

		await waitFor(() => expect(backend.calls("PUT", "mindmap/nodes/a")).toHaveLength(1));
		expect(Object.keys(backend.calls("PUT", "mindmap/nodes/a")[0]!.body as object).sort()).toEqual(["mark", "version"]);
		expect(screen.getByTestId(ids.detail)).toBeTruthy();
	});
});
