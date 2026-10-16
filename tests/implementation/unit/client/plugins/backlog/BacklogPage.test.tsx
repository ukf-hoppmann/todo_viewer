import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { PriorityFilter, StatusFilter } from "../../../../../../client/src/plugins/backlog/Filters";
import BacklogPage from "../../../../../../client/src/plugins/backlog/pages/BacklogPage";
import { backlogTestIds as ids } from "../../../../../../client/src/plugins/backlog/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { detail, item } from "../../../../../helpers/client/backlogFixtures";
import { fakeWorkspaceBackend, project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const items = [
	item("e1", { type: "Epic", progress: { done: 1, total: 3 }, status: "In progress", priority: "Urgent" }),
	item("s1", { type: "Story", parent_uid: "e1", status: "Completed" }),
	item("s2", { type: "Story", parent_uid: "e1", progress: { done: 0, total: 1 } }),
	item("t1", { parent_uid: "s2" }),
	item("opt", { type: "Story", parent_uid: "e1", required_for_parent: false }),
	item("rej", { type: "Story", parent_uid: "e1", status: "Rejected" }),
	item("other", { project_uid: "p0", title: "Allgemeines" }),
];

const node = (uid: string) => screen.getByTestId(sharedTestIds.treeNode(uid));

afterEach(cleanup);

async function renderPage(options: Parameters<typeof fakeWorkspaceBackend>[0] = {}) {
	const backend = fakeWorkspaceBackend({ projects, backlog: items, details: { e1: detail("e1", { title: "Titel e1" }) }, ...options });
	await renderWorkspace(
		<>
			<StatusFilter />
			<PriorityFilter />
			<BacklogPage />
		</>,
		{ backend },
	);
	return backend;
}

describe("BacklogPage: tree", () => {
	it("shows a tree per project with the progress of the project and of the items", async () => {
		await renderPage();

		const viewer = await screen.findByTestId(ids.project("p1"));
		// optional and rejected items do not count: e1, s2, t1 and the completed s1 → 1 of 4... (e1, s1, s2, t1)
		expect(screen.getByTestId(ids.projectProgress("p1")).textContent).toBe("Viewer (1/4)");
		expect(screen.getByTestId(ids.projectProgress("p0")).textContent).toBe("Allgemein (0/1)");
		expect(within(viewer).getByTestId(sharedTestIds.treeNode("e1")).textContent).toContain("Titel e1");
		expect(within(node("e1")).getByTestId(sharedTestIds.progressRing).getAttribute("aria-label")).toBe("1/3");
	});

	it("hides finished items by default but keeps them in the progress, and shows them when the filter is switched", async () => {
		await renderPage();
		await screen.findByTestId(ids.project("p1"));

		await screen.findByTestId(sharedTestIds.treeNode("s2"));
		expect(screen.queryByTestId(sharedTestIds.treeNode("s1"))).toBeNull();
		expect(screen.queryByTestId(sharedTestIds.treeNode("rej"))).toBeNull();
		expect(screen.getByTestId(ids.projectProgress("p1")).textContent).toBe("Viewer (1/4)");

		fireEvent.click(screen.getByTestId(sharedTestIds.filterOption("Completed")));
		await waitFor(() => expect(screen.getByTestId(sharedTestIds.treeNode("s1"))).toBeTruthy());
	});

	it("draws an optional child dashed", async () => {
		await renderPage({ documents: { backlog: { hiddenStatuses: [], collapsed: [] } } });

		await waitFor(() => expect(screen.getByTestId(sharedTestIds.treeNode("opt"))).toBeTruthy());

		expect(node("opt").getAttribute("data-dashed")).toBe("true");
		expect(node("s2").getAttribute("data-dashed")).toBeNull();
	});

	it("filters by the search text of the workspace", async () => {
		await renderPage({ documents: { backlog: { hiddenStatuses: [] }, workspace: { search: "allgem" } } });

		await screen.findByTestId(sharedTestIds.treeNode("other"));
		expect(screen.queryByTestId(ids.project("p1"))).toBeNull();
	});

	it("shows only the projects that are switched on", async () => {
		await renderPage({ documents: { workspace: { hidden: ["p0"] } } });

		await screen.findByTestId(ids.project("p1"));
		expect(screen.queryByTestId(ids.project("p0"))).toBeNull();
	});

	it("says so when nothing is shown", async () => {
		await renderPage({ backlog: [] });

		expect((await screen.findByTestId(ids.empty)).textContent).toContain("Keine Items");
	});

	it("remembers the folded items in the UI state of the server", async () => {
		const backend = await renderPage({ documents: { backlog: { hiddenStatuses: [] } } });
		await screen.findByTestId(sharedTestIds.treeNode("s2"));

		fireEvent.click(screen.getByTestId(sharedTestIds.treeToggle("e1")));

		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.treeNode("s2"))).toBeNull());
		await waitFor(async () => {
			const { flushUiState } = await import("../../../../../../client/src/core/ui-state/uiState");
			await flushUiState(backend.store);
			expect((backend.documents.get("backlog") as { collapsed?: string[] }).collapsed).toEqual(["e1"]);
		});
	});
});

describe("BacklogPage: folding buttons", () => {
	it("folds all epics and then unfolds them, for the marked project only", async () => {
		await renderPage({ documents: { backlog: { hiddenStatuses: [] }, workspace: { marked: "p1" } } });
		await screen.findByTestId(sharedTestIds.treeNode("s2"));

		fireEvent.click(screen.getByTestId(ids.collapse("Epic")));
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.treeNode("s2"))).toBeNull());
		expect(screen.getByTestId(ids.collapse("Epic")).textContent).toBe("Epics aufklappen");
		fireEvent.click(screen.getByTestId(ids.collapse("Epic")));

		await waitFor(() => expect(screen.getByTestId(sharedTestIds.treeNode("s2"))).toBeTruthy());
	});

	it("disables the button of a type nobody has children of", async () => {
		await renderPage({ backlog: [item("only", { type: "Epic" })] });
		await screen.findByTestId(ids.project("p1"));

		expect((screen.getByTestId(ids.collapse("Epic")) as HTMLButtonElement).disabled).toBe(true);
	});
});

describe("BacklogPage: selection", () => {
	it("shows the detail panel of the selected item and remembers the selection", async () => {
		const backend = await renderPage({ documents: { backlog: { hiddenStatuses: [] } } });
		expect((await screen.findByTestId(ids.detailEmpty)).textContent).toContain("Ein Item");

		fireEvent.click(await screen.findByTestId(sharedTestIds.treeNode("e1")));

		await waitFor(() => expect(screen.getByTestId(sharedTestIds.detailTitle).textContent).toBe("E1 — Titel e1"));
		await waitFor(async () => {
			const { flushUiState } = await import("../../../../../../client/src/core/ui-state/uiState");
			await flushUiState(backend.store);
			expect((backend.documents.get("backlog") as { selected?: string }).selected).toBe("e1");
		});
	});
});
